"""Independent host-only LC989 transport checks; never imports author code."""
import base64
import hashlib
import json
import math
import re

PROFILE = "lc989-digits10000-positive47-number-bigint-to-decimal-array-v1"
ENTRY = "0989:javascript"
TAG = "__gamma_uint_decimal_v1__"
SAFE = 2**53 - 1
MAXIMUM = 10**47 - 1
COMMANDS = {
    "python": ["/usr/bin/python3", "harness.py"],
    "javascript": ["/usr/bin/node", "--jitless", "--max-old-space-size=64", "harness.cjs"],
}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    need(type(raw) in (bytes, str), "Exact byte or text buffer required")
    return hashlib.sha256(raw.encode() if type(raw) is str else raw).hexdigest()


def compact(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False))


def unique(pairs):
    result = {}
    for name, value in pairs:
        need(name not in result, "Duplicate JSON field")
        result[name] = value
    return result


def bad_constant(value):
    raise ValueError("Nonfinite JSON constant")


def parse(raw, canonical=False):
    need(type(raw) in (bytes, str), "JSON buffer required")
    try:
        text = raw.decode("ascii" if canonical else "utf-8") if type(raw) is bytes else raw
        if canonical:
            text.encode("ascii")
        result = json.loads(text, object_pairs_hook=unique, parse_constant=bad_constant)
        need(not canonical or compact(result) == text, "Noncanonical JSON")
        return result
    except (UnicodeError, ValueError, RecursionError) as error:
        raise ValueError("Invalid JSON buffer") from error


def uint(value):
    need(type(value) is dict and set(value) == {TAG}, "Positive decimal envelope required")
    text = value[TAG]
    need(type(text) is str and re.fullmatch(r"[1-9][0-9]{0,46}", text, re.ASCII), "Canonical positive47 required")
    return int(text)


def digits(value, maximum=10000):
    need(type(value) is list and 1 <= len(value) <= maximum and
         all(type(n) is int and 0 <= n <= 9 for n in value), "Bounded exact digit array required")
    return list(value)


def encode_calls(cases):
    need(type(cases) is list and 1 <= len(cases) <= 4, "One to four cases required")
    calls = []
    for case in cases:
        need(type(case) is dict and type(case.get("args")) is list and len(case["args"]) == 2 and
             type(case["args"][1]) is int and 1 <= case["args"][1] <= MAXIMUM and
             type(case.get("kwargs", {})) is dict and not case.get("kwargs"), "Exact positional arguments required")
        calls.append({"args": [digits(case["args"][0]), {TAG: str(case["args"][1])}]})
    raw = compact({"profile": PROFILE, "entry": "Solution.addToArrayForm", "calls": calls}).encode()
    need(len(raw) <= 128 * 1024, "Request size exceeded")
    return raw


def request_cases(raw):
    need(type(raw) is bytes and len(raw) <= 128 * 1024, "Bounded request bytes required")
    value = parse(raw, canonical=True)
    need(type(value) is dict and set(value) == {"profile", "entry", "calls"} and
         value["profile"] == PROFILE and value["entry"] == "Solution.addToArrayForm" and
         type(value["calls"]) is list and 1 <= len(value["calls"]) <= 4, "Exact request framing required")
    cases = []
    for call in value["calls"]:
        need(type(call) is dict and set(call) == {"args"} and type(call["args"]) is list and len(call["args"]) == 2,
             "Exact call framing required")
        cases.append({"args": [digits(call["args"][0]), uint(call["args"][1])]})
    need(encode_calls(cases) == raw, "Canonical request roundtrip differs")
    return cases


def records(raw, count):
    need(type(raw) is bytes and len(raw) <= 512 * 1024 and type(count) is int and 1 <= count <= 4,
         "Bounded stdout bytes/count required")
    rows = [parse(line, canonical=True) for line in raw.splitlines()]
    need(len(rows) == count + 1 and type(rows[-1]) is dict and set(rows[-1]) == {"done"} and
         type(rows[-1]["done"]) is int and rows[-1]["done"] == count, "Exact completion required")
    for index, row in enumerate(rows[:-1]):
        need(type(row) is dict and type(row.get("i")) is int and row["i"] == index and "done" not in row,
             "Exact ordered index required")
    return rows


def decode(raw, cases, language="javascript"):
    need(language == "javascript", "Only989JavaScript qualification supported")
    encode_calls(cases)
    rows = records(raw, len(cases))
    fields = {"i", "result", "args_before", "args_after", "argument_runtime_types", "argument_element_runtime_type",
              "result_runtime_type", "result_element_runtime_type", "input_object_count", "returned_input_ids",
              "input_node_values_preserved", "input_identity_order_preserved", "result_is_first_arg"}
    result = []
    for row, case in zip(rows[:-1], cases):
        need(set(row) == fields, "Exact observation fields required")
        expected_kind = "number" if case["args"][1] <= SAFE else "bigint"
        need(row["argument_runtime_types"] == ["array", expected_kind] and
             row["argument_element_runtime_type"] == row["result_element_runtime_type"] == "number" and
             row["result_runtime_type"] == "array", "Exact input/output runtime types required")
        need(type(row["input_object_count"]) is int and row["input_object_count"] == 1 and
             type(row["returned_input_ids"]) is list and row["returned_input_ids"] == [] and
             row["input_node_values_preserved"] is True and row["input_identity_order_preserved"] is True and
             row["result_is_first_arg"] is False, "Mutation/order/alias observations differ")
        decoded = dict(row, result=digits(row["result"], 10001))
        for field in ("args_before", "args_after"):
            need(type(row[field]) is list and len(row[field]) == 2, "Two argument slots required")
            decoded[field] = [digits(row[field][0]), uint(row[field][1])]
            need(digest(decoded[field]) == digest(case["args"]), "Exact argument roundtrip required")
        result.append(decoded)
    return result + [rows[-1]]


def native(value):
    fields = {"exit_code", "signal", "stdout", "stderr", "wall_seconds", "timed_out",
              "output_limit_exceeded", "notes", "ok"}
    need(type(value) is dict and set(value) == fields, "Full native status required")
    need(type(value["exit_code"]) is int and value["exit_code"] == 0 and
         value["signal"] is None and value["timed_out"] is False and
         value["output_limit_exceeded"] is False and value["ok"] is True and
         type(value["notes"]) is list and not value["notes"] and
         type(value["wall_seconds"]) in (int, float) and
         math.isfinite(value["wall_seconds"]) and 0 <= value["wall_seconds"] <= 8,
         "Native execution not clean")
    decoded = dict(value)
    for stream in ("stdout", "stderr"):
        blob = value[stream]
        need(type(blob) is dict and set(blob) == {"encoding", "data", "sha256", "byte_count"} and
             blob["encoding"] == "base64" and type(blob["data"]) is str and
             type(blob["byte_count"]) is int, "Full stream envelope required")
        try:
            raw = base64.b64decode(blob["data"], validate=True)
        except (ValueError, TypeError) as error:
            raise ValueError("Malformed base64") from error
        need(base64.b64encode(raw).decode() == blob["data"] and
             sha(raw) == blob["sha256"] and len(raw) == blob["byte_count"] and
             len(raw) <= 4 * 1024**2, "Lossless stream binding required")
        decoded[stream] = raw
    return decoded


def payload(value, raw, frozen_sources, relative, cases=None, control=None):
    """Reconstruct candidate intent; controls bind their exact frozen request bytes."""
    need(relative in frozen_sources, "Exact frozen source required")
    need(type(value) is dict and set(value) == {"schema", "argv", "expected_calls", "files_utf8", "input_file_sha256", "binding"} and
         value["schema"] == "algsolve.exact-retained-call-payload.v1", "Exact payload schema required")
    files = value["files_utf8"]
    need(type(files) is dict and set(files) == {"candidate.cjs", "harness.cjs", "calls.json"} and
         all(type(v) is str for v in files.values()), "Exact file set required")
    hashes = {n: sha(v) for n, v in files.items()}
    need(hashes["candidate.cjs"] == frozen_sources[relative] and hashes["harness.cjs"] == frozen_sources["harness.cjs"],
         "Candidate or harness differs")
    if control is None:
        request = encode_calls(cases); count = len(cases); kind = "candidate"; name = None
    else:
        need(cases is None and control["source"] == relative, "Exact control identity required")
        request = files["calls.json"].encode(); name = control["name"]; kind = "control"
        need(sha(request) == frozen_sources[control["request"]], "Control request differs")
        count = None if control["invalid_request"] else len(request_cases(request))
    need(files["calls.json"].encode() == request, "Actual request differs")
    binding = {"kind": kind, "source": relative, "source_sha256": frozen_sources[relative],
               "harness_sha256": frozen_sources["harness.cjs"], "codec_sha256": frozen_sources["codec.py"],
               "request_sha256": sha(request), "expected_calls": count, "argv": COMMANDS["javascript"],
               "control_name": name}
    need(digest(value["binding"]) == digest(binding) == digest(raw["payload_binding"]), "Payload authority differs")
    need(digest(value["expected_calls"]) == digest(count) == digest(raw["expected_calls"]) and
         value["argv"] == raw["argv"] == COMMANDS["javascript"] and
         value["input_file_sha256"] == raw["input_file_sha256"] == hashes, "Actual file/argv/count differs")
    need(raw["phase"] == ("candidate-javascript" if control is None else "control-" + name) and
         raw["expectations_supplied"] is False and raw["sandbox_returned"] is True, "Invocation phase differs")
    return binding
