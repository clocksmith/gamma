"""Independent host-only LC1056 transport checks; never imports author code."""
import base64
import hashlib
import json
import math
import re

PROFILE = "lc1056-uint19-number-bigint-to-boolean-v1"
ENTRY = "1056:javascript"
TAG = "__gamma_uint_decimal_v1__"
SAFE = 2**53 - 1
MAXIMUM = 10**19 - 1
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
    need(type(value) is dict and set(value) == {TAG}, "Decimal envelope required")
    text = value[TAG]
    need(type(text) is str and re.fullmatch(r"0|[1-9][0-9]{0,18}", text, re.ASCII),
         "Canonical uint19 required")
    return int(text)


def encode_calls(cases):
    need(type(cases) is list and 1 <= len(cases) <= 4, "One to four cases required")
    calls = []
    for case in cases:
        need(type(case) is dict and type(case.get("args")) is list and
             len(case["args"]) == 1 and type(case["args"][0]) is int and
             0 <= case["args"][0] <= MAXIMUM and
             type(case.get("kwargs", {})) is dict and not case.get("kwargs"),
             "One exact uint19 positional argument required")
        calls.append({"args": [{TAG: str(case["args"][0])}]})
    return compact({"profile": PROFILE, "entry": "Solution.confusingNumber", "calls": calls}).encode()


def records(raw, count):
    need(type(raw) is bytes and type(count) is int and 1 <= count <= 4, "Raw bytes/count required")
    rows = [parse(line, canonical=True) for line in raw.splitlines()]
    need(len(rows) == count + 1 and type(rows[-1]) is dict and
         set(rows[-1]) == {"done"} and type(rows[-1]["done"]) is int and
         rows[-1]["done"] == count, "Exact completion required")
    for index, row in enumerate(rows[:-1]):
        need(type(row) is dict and type(row.get("i")) is int and
             row["i"] == index and "done" not in row, "Exact ordered index required")
    return rows


def decode(raw, cases, language):
    need(language in ("python", "javascript"), "Explicit language required")
    encode_calls(cases)
    rows = records(raw, len(cases))
    fields = {"i", "result", "args_before", "args_after", "argument_runtime_types",
              "result_runtime_type", "input_object_count", "returned_input_ids",
              "input_node_values_preserved"}
    result = []
    for row, case in zip(rows[:-1], cases):
        need(set(row) == fields and type(row["result"]) is bool, "Strict Boolean observation required")
        expected_kind = "int" if language == "python" else (
            "number" if case["args"][0] <= SAFE else "bigint")
        need(row["argument_runtime_types"] == [expected_kind] and
             row["result_runtime_type"] == ("bool" if language == "python" else "boolean"),
             "Exact input and result runtime types required")
        need(type(row["input_object_count"]) is int and row["input_object_count"] == 0 and
             row["returned_input_ids"] == [] and row["input_node_values_preserved"] is True,
             "Primitive alias observations differ")
        decoded = dict(row)
        for field in ("args_before", "args_after"):
            need(type(row[field]) is list and len(row[field]) == 1, "One argument slot required")
            decoded[field] = [uint(row[field][0])]
            need(decoded[field] == case["args"], "Exact argument roundtrip required")
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


def payload(value, raw, frozen_sources, relative, language, cases=None, invalid=None):
    """Check retained actual payload against independently reconstructed intent."""
    need(language in COMMANDS and relative in frozen_sources, "Exact frozen source required")
    need(type(value) is dict and set(value) == {
        "schema", "argv", "expected_calls", "files_utf8", "input_file_sha256", "binding"},
        "Exact retained payload schema required")
    need(value["schema"] == "algsolve.exact-retained-call-payload.v1", "Wrong payload schema")
    harness = "harness.py" if language == "python" else "harness.cjs"
    candidate = "candidate.py" if language == "python" else "candidate.cjs"
    files = value["files_utf8"]
    expected_files = {harness, candidate, "calls.json"} | ({"codec.py"} if language == "python" else set())
    need(type(files) is dict and set(files) == expected_files and
         all(type(v) is str for v in files.values()), "Exact sandbox file set required")
    hashes = {name: sha(text) for name, text in files.items()}
    need(hashes[candidate] == frozen_sources[relative] and
         hashes[harness] == frozen_sources[harness] and
         (language != "python" or hashes["codec.py"] == frozen_sources["codec.py"]),
         "Candidate/harness/codec drift")
    if invalid is None:
        request = encode_calls(cases)
        count = len(cases)
        kind = "frozen-source"
        invalid_name = None
    else:
        need(cases is None and invalid["source"] == relative and invalid["language"] == language,
             "Exact invalid control required")
        request = files["calls.json"].encode()
        need(sha(request) == frozen_sources[invalid["payload"]], "Invalid control request drift")
        count, kind, invalid_name = None, "frozen-invalid-request", invalid["name"]
    need(files["calls.json"].encode() == request, "Actual request differs")
    binding = {"kind": kind, "language": language, "source_relative_path": relative,
               "source_sha256": frozen_sources[relative], "harness_relative_path": harness,
               "harness_sha256": frozen_sources[harness], "codec_sha256": frozen_sources["codec.py"],
               "request_sha256": sha(request), "expected_calls": count,
               "argv": COMMANDS[language], "invalid_control_name": invalid_name}
    need(digest(value["binding"]) == digest(binding) and
         digest(raw["payload_binding"]) == digest(binding), "Source binding authority differs")
    need(digest(value["expected_calls"]) == digest(count) and
         digest(raw["expected_calls"]) == digest(count) and
         value["argv"] == raw["argv"] == COMMANDS[language] and
         value["input_file_sha256"] == raw["input_file_sha256"] == hashes,
         "Actual files/argv/count differ")
    need(raw["phase"] == "integer1056-" + language and raw["expectations_supplied"] is False and
         raw["sandbox_returned"] is True, "Invocation phase/status differs")
    return binding
