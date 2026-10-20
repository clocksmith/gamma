"""Saved-evidence-only replay for the one frozen989 qualification."""
import base64
from pathlib import Path
from . import campaign_989_transport as t
from .campaign_989_integer import FREEZE, ACTIVATION, READER, AUTHOR, read, check

need = t.need


def replay(bound, refs):
    # Trusted installed judge only. No source, harness, codec or runner imports.
    from . import campaign_exact_integer as common
    frozen, root = bound["freeze"], bound["_root"]
    allowed = bound["_allowed"]
    index = bound["evidence_index"]
    need(index.get("schema") == "algsolve.hash-bound-evidence-index.v1" and
         index.get("freeze", {}).get("sha256") == FREEZE, "Exact complete raw index required")
    items = index.get("results")
    need(type(items) is list and bool(items), "Raw evidence inventory missing")
    inventory = {}
    for item in items:
        path = item["path"]
        need(path not in inventory, "Duplicate evidence path")
        inventory[path] = item
        read(item)
        refs.append(item)
    def load(path):
        need(str(path) in inventory, "Unindexed qualification artifact")
        return check(inventory[str(path)])
    def indexed(name):
        item = allowed[name]
        need(inventory.get(item["path"], {}).get("sha256") == item["sha256"],
             "Required proof absent from complete index")
        return bound[name]
    summary, seal = indexed("summary"), indexed("execution_seal")
    output = Path(allowed["summary"]["path"]).parent
    need(output.parent == root and output.name == "results-attempt-001", "Exact result location required")
    manifest_sha = allowed["toolchain_manifest"]["sha256"]
    need(seal.get("schema") == "algsolve.integer989-execution-seal.v1" and
         seal.get("freeze_sha256") == FREEZE and seal.get("profile") == t.PROFILE and
         seal.get("root_approval_sha256") == allowed["root_approval"]["sha256"] and
         seal.get("toolchain_manifest_sha256") == manifest_sha and
         seal.get("reader_test_pins_sha256") == frozen["sources"]["approved-test-pins.json"] and
         seal.get("expected_outputs_in_sandbox") is False, "Execution seal differs")
    hashes = {str(root / name): value for name, value in frozen["sources"].items()}
    for item in frozen["host_dependencies"] + frozen["authority_dependencies"]:
        prior = hashes.setdefault(item["path"], item["sha256"])
        need(prior == item["sha256"], "Conflicting dependency identities")
    receipts = seal.get("retained_import_receipts")
    unused = {"algsolve.importers", "algsolve.public_examples", "algsolve.values"}
    expected_loaded = set(frozen["retained_imports"]) - unused
    need(type(receipts) is dict and set(receipts) == expected_loaded and len(receipts) == 18,
         "Full retained module receipts required")
    for name in expected_loaded:
        path = frozen["retained_imports"][name]
        need(receipts[name] == {"path": path, "sha256": hashes[path], "retained_bytes_compiled": True},
             "Retained module receipt differs from freeze")
    retained = {"retained_runtime_modules": len(receipts),
                "retained_runtime_module_receipts_sha256": t.digest(receipts),
                "authority_metadata_from_verified_retained_bytes": True,
                "bootstrap_stdlib_retained_import_claimed": False}
    def reader(value, stage):
        need(type(value) is dict and value.get("schema") == "algsolve.batch-reader-gate.v1" and
             value.get("stage") == stage and value.get("passed") is True and
             value.get("activation_sha256") == ACTIVATION and
             value.get("shared_reader_sha256") == READER and
             type(value.get("selected_claims")) is int and value["selected_claims"] == 1 and
             type(value.get("ledger_revision_observed")) is int and value["ledger_revision_observed"] == 1677 and
             type(value.get("ledger_raw_bytes")) is int and value["ledger_raw_bytes"] == 452316655 and
             value.get("ledger_raw_sha256") == "0fafb5e80deaa00a3564a17e7989e87ad79814eeeca6d9ace09e7beb853856ca" and
             all(type(value.get(k)) is int and value[k] == 0 for k in
                 ("candidate_runs", "corpus_records_decoded", "imported_test_files_loaded")),
             "Reader proof incomplete")
    runtime = {"schema": "algsolve.toolchain-verification.v1", "passed": True,
               "executable_count": 4, "measured_identity_count": 59,
               "host_interpreter_matches_sandbox_python": True, "complete_dynamic_closure_claimed": False}
    def proof(value, stage):
        need(value.get("contract_sha256") == FREEZE and
             value.get("toolchain_manifest_sha256") == manifest_sha and
             type(value.get("frozen_files_checked")) is int and value["frozen_files_checked"] == 92 and
             type(value.get("host_dependencies_checked")) is int and value["host_dependencies_checked"] == 115 and
             t.digest(value.get("runtime")) == t.digest(runtime) and
             t.digest(value.get("retained_imports")) == t.digest(retained), "Complete boundary proof differs")
        reader(value.get("reader"), stage)
    final = indexed("final_boundary")
    proof(final, "run-final")
    need(summary.get("final_boundary_sha256") == allowed["final_boundary"]["sha256"] and
         summary.get("schema") == "algsolve.integer989-qualification-summary.v1" and
         summary.get("status") == "completed" and summary.get("qualification_passed") is True and
         summary.get("freeze_sha256") == FREEZE and summary.get("profile") == t.PROFILE and
         type(summary.get("per_call_boundary_count")) is int and summary["per_call_boundary_count"] == 39,
         "Success summary not bound to complete final proof")
    seen = set()
    def call(number, relative=None, cases=None, control=None):
        need(type(number) is int and number not in seen, "Duplicate call")
        seen.add(number)
        raw = load(output / f"boundary-{number:05d}.json")
        need(raw.get("schema") == "algsolve.per-call-boundary.v1" and
             type(raw.get("call")) is int and raw["call"] == number and
             "error_type" not in raw and "after_error_type" not in raw, "Raw invocation incomplete")
        proof(raw["before"], "before-" + raw["phase"])
        proof(raw["after"], "after-" + raw["phase"])
        payload_ref = raw.get("retained_payload")
        expected_path = str(output / f"payload-{number:05d}.json")
        need(payload_ref.get("path") == expected_path and
             inventory.get(expected_path, {}).get("sha256") == payload_ref.get("sha256"),
             "Retained payload reference differs")
        payload_bytes = read(payload_ref)
        need(type(payload_ref.get("encoded_bytes")) is int and
             len(payload_bytes) == payload_ref["encoded_bytes"] <= 131072, "Payload size differs")
        payload = t.parse(payload_bytes)
        result = t.native(raw["sandbox_result"])
        if relative is None:
            wanted = {"schema": "algsolve.exact-retained-call-payload.v1",
                      "argv": ["/usr/bin/python3", "-c", "print(42)"], "expected_calls": None,
                      "files_utf8": {}, "input_file_sha256": {}, "binding": {"kind": "fixed-probe"}}
            need(t.digest(payload) == t.digest(wanted) and
                 raw["phase"] == "sandbox-probe" and raw["argv"] == wanted["argv"] and
                 raw["expected_calls"] is None and raw["payload_binding"] == wanted["binding"] and
                 raw["input_file_sha256"] == {} and raw["expectations_supplied"] is False and
                 raw["sandbox_returned"] is True and result["stdout"] == b"42\n" and
                 raw["protocol"] == {"valid": True, "kind": "fixed-probe-or-input-rejection-raw"},
                 "Fixed probe differs")
        else:
            t.payload(payload, raw, frozen["sources"], relative, cases, control)
            expected_protocol = ({"valid": True, "kind": "fixed-probe-or-input-rejection-raw"} if control and control["invalid_request"] else
                                 {"expected_calls": raw["expected_calls"], "valid": True, "reason": None})
            need(t.digest(raw["protocol"]) == t.digest(expected_protocol), "Framing protocol differs")
            if not (control and control["invalid_request"]):
                t.records(result["stdout"], raw["expected_calls"])
        return result, raw, payload
    def score(result, decoded, cases):
        fields = {k: result[k] for k in ("exit_code", "signal", "stderr", "wall_seconds",
                                        "timed_out", "output_limit_exceeded", "notes")}
        fields["stdout"] = ("\n".join(t.compact(row) for row in decoded) + "\n").encode()
        native = common.sandbox.SandboxResult(**fields)
        return common.judge._score_functional(native, common.validate.functional_tests(cases)).to_dict()
    call(1)
    number, controls = 2, bound["controls"]
    control_rows = []
    need(type(controls.get("controls")) is list and len(controls["controls"]) == 18, "Exact controls required")
    for item in controls["controls"]:
        result, raw, payload = call(number, item["source"], control=item)
        kind = control_result(item, result["stdout"], payload["files_utf8"]["calls.json"].encode())
        control_rows.append({"name": item["name"], "call_id": number, "passed": True,
                             "kind": kind, "raw_boundary_file": f"boundary-{number:05d}.json"})
        number += 1
    need(number == 20 and t.digest(load(output / "controls-summary.json")) ==
         t.digest({"passed": True, "calls": control_rows}) and
         t.digest(summary.get("controls")) == t.digest(control_rows), "Control coverage differs")
    need(type(summary.get("rows")) is list and len(summary["rows"]) == 1, "Only989JavaScript qualification required")
    for language_row, language, relative in zip(summary["rows"], ("javascript",), ("candidate.js",)):
        chunks, official = [], 0
        for group in bound["_groups"]:
            for offset in range(0, len(group["tests"]), 4):
                cases = group["tests"][offset:offset+4]
                result, raw, _ = call(number, relative, cases)
                decoded = t.decode(result["stdout"], cases, language)
                verdict = score(result, decoded, cases)
                need(verdict["passed"] is True, "Unchanged host comparison failed")
                individual = []
                for position, case in enumerate(cases):
                    one = score(result, [dict(decoded[position], i=0), {"done": 1}], [case])
                    admissible = case["args"][1] <= 10000 and (len(case["args"][0]) == 1 or case["args"][0][0] != 0)
                    official += admissible
                    need(one["passed"] is True, "Individual host comparison failed")
                    individual.append({"case": offset+position, "official_domain": admissible,
                                       "passed": True, "exact_argument_roundtrip": True,
                                       "runtime_types_valid": True})
                chunk = {"language": language, "group": group["name"], "offset": offset,
                         "call_id": number, "raw_boundary_file": f"boundary-{number:05d}.json",
                         "protocol": raw["protocol"], "transport_error": None, "sandbox_ok": True,
                         "output_limit_exceeded": False, "verdict": verdict, "individual": individual,
                         "decoded_observations": decoded}
                path = output / f'{language}-{group["name"]}-{offset}.json'
                need(t.digest(load(path)) == t.digest(chunk), "Saved decoded chunk differs from raw replay")
                chunks.append(dict(inventory[str(path)], cases=len(cases), passed=True,
                                   tests_passed=len(cases), call_id=number))
                number += 1
        expected = {"language": language, "source_sha256": frozen["sources"][relative],
                    "chunks": chunks, "passed": True, "tests_total": 78, "tests_passed": 78}
        need(t.digest(language_row) == t.digest(expected) and official == 30,
             "Qualification coverage/domain split differs")
    need(number == 40 and seen == set(range(1, 40)), "Full39-call coverage missing")
    names = {Path(p).name for p in inventory if Path(p).parent == output}
    need({n for n in names if n.startswith("boundary-")} ==
         {f"boundary-{i:05d}.json" for i in seen} | {"boundary-final.json"} and
         {n for n in names if n.startswith("payload-")} == {f"payload-{i:05d}.json" for i in seen},
         "Unexplained/duplicate raw evidence")
    _lifecycle(bound, indexed, reader, runtime, hashes)
    return {"cases_each": 78, "passed_each": 78, "calls": 39, "controls": 18}


def control_result(item, stdout, request):
    """Independent interpretation of each frozen synthetic negative/positive control."""
    expected = item["expected"]
    if item["invalid_request"]:
        rows = [t.parse(line, canonical=True) for line in stdout.splitlines()]
        need(t.digest(rows) == t.digest([expected["single_record"]]) and
             expected.get("candidate_source_must_not_be_loaded") is True, "Whole packet rejection differs")
        return "whole-packet-rejection"
    cases = t.request_cases(request)
    if "decoded_result" in expected:
        rows = t.decode(stdout, cases)
        need(len(rows) == 2 and t.digest(rows[0]["result"]) == t.digest(expected["decoded_result"]),
             "Positive runtime/type control differs")
        return "valid-control"
    rows = t.records(stdout, len(cases))
    need(len(cases) == 1, "One negative control case required")
    if "row_error" in expected:
        need(t.digest(rows[0]) == t.digest({"i": 0, "error": expected["row_error"]}), "Exact output error differs")
    else:
        row = rows[0]
        need("error" not in row and (
             t.digest(row.get("args_before")) != t.digest(row.get("args_after")) or
             row.get("input_node_values_preserved") is False or row.get("input_identity_order_preserved") is False or
             row.get("result_is_first_arg") is True or t.digest(row.get("returned_input_ids")) == t.digest([0])),
             "Specific mutation or alias evidence required")
        repaired = dict(row, args_after=row.get("args_before"), input_node_values_preserved=True,
                        input_identity_order_preserved=True, result_is_first_arg=False, returned_input_ids=[])
        t.decode((t.compact(repaired) + "\n" + t.compact({"done": 1}) + "\n").encode(), cases)
    try:
        t.decode(stdout, cases)
    except ValueError:
        return "invalid-output-or-effect-rejected"
    raise ValueError("Invalid output/effect accepted")


def _lifecycle(bound, indexed, reader, runtime, hashes):
    """Require the detached runner's actual exit and fresh final launcher proof."""
    allowed = bound["_allowed"]
    preflight, child = indexed("launch_preflight"), indexed("child_identity")
    terminal, output, final = indexed("runner_exit"), indexed("runner_output"), indexed("launch_final")
    receipts = preflight.get("retained_import_receipts")
    mapping = bound["freeze"]["retained_imports"]
    need(type(receipts) is dict and
         {"toolchain", "reader_gate", "evidence_budget", "runtime_adapter",
          "algsolve", "algsolve.judge", "algsolve.judge.sandbox"} == set(receipts),
         "Launcher retained receipts incomplete")
    need(preflight.get("screen_sha256") == "1eabc87c9b22f8aba953aa968a8ac6be76d6a1539f5d7e000b180d5a946aa72b" and
         preflight.get("environment_rewritten") is False and
         t.digest(preflight.get("host_environment")) == t.digest(bound["toolchain_manifest"]["host_environment"]),
         "Measured launcher environment differs")
    for name, receipt in receipts.items():
        need(receipt == {"path": mapping[name], "sha256": hashes[mapping[name]],
                         "retained_bytes_compiled": True}, "Launcher retained module binding differs")
    retained = {"retained_runtime_modules": len(receipts),
                "retained_runtime_module_receipts_sha256": t.digest(receipts),
                "authority_metadata_from_verified_retained_bytes": True,
                "bootstrap_stdlib_retained_import_claimed": False}
    need(terminal.get("status") == "process-exited" and type(terminal.get("child_exit_code")) is int and
         terminal["child_exit_code"] == 0 and terminal.get("child_signal") is None and
         terminal.get("capture_limit_exceeded") is False and terminal.get("final_boundary_passed") is True and
         terminal.get("final_boundary_sha256") == allowed["launch_final"]["sha256"],
         "Actual clean runner exit and launcher final proof required")
    need(output.get("encoding") == "base64" and type(output.get("data")) is str and
         output.get("capture_complete") is True and output.get("capture_limit_exceeded") is False and
         type(output.get("byte_count")) is int, "Complete runner output required")
    raw = base64.b64decode(output["data"], validate=True)
    need(base64.b64encode(raw).decode() == output["data"] and len(raw) == output["byte_count"] <= 65536 and
         t.sha(raw) == output["sha256"] == terminal["output_sha256"] and
         type(terminal["output_bytes"]) is int and terminal["output_bytes"] == len(raw),
         "Runner output hash/length differs")
    lines = raw.splitlines()
    need(len(lines) == 1 and t.parse(lines[0]) == {
        "status": "completed", "qualification_passed": True,
        "summary_sha256": allowed["summary"]["sha256"]}, "Runner summary announcement differs")
    command = preflight.get("child_argv")
    need(command == child.get("child_argv") and type(command) is list and
         command[:5] == ["/usr/bin/taskset", "-c", "12", "/usr/bin/python3", "-B"] and
         len(command) == 13 and command[5] == "-c" and
         type(command[6]) is str and
         t.sha(command[6]) == "3f55d0f2ef7fd039ab9cf5a4a223183294590125bb573a797cdb3632ca1e1173" and
         command[-4:] == ["results-attempt-001", FREEZE, allowed["root_approval"]["path"],
                         allowed["root_approval"]["sha256"]] and
         command[-6] == str(bound["_root"] / "run.py") and
         command[-5] == bound["freeze"]["sources"]["run.py"],
         "Frozen runner argv differs")
    for name in ("launcher",):
        _process(preflight.get(name))
    _process(child.get("child"))
    need(preflight["launcher"]["boot_id"] == child["child"]["boot_id"] and
         preflight["launcher"]["pid"] != child["child"]["pid"], "Launcher/child identity differs")
    for value, stage in ((preflight["initial_boundary"], "launcher-before-output"), (final, "launcher-final")):
        need(value.get("stage") == stage and value.get("freeze_sha256") == FREEZE and
             value.get("root_approval_sha256") == allowed["root_approval"]["sha256"] and
             t.digest(value.get("runtime")) == t.digest(runtime) and
             t.digest(value.get("retained_imports")) == t.digest(retained),
             "Launcher proof differs")
        reader(value.get("reader"), stage)


def _process(value):
    need(type(value) is dict and type(value.get("pid")) is int and value["pid"] > 0 and
         type(value.get("start_time_ticks")) is str and value["start_time_ticks"].isdigit() and
         type(value.get("boot_id")) is str and len(value["boot_id"]) == 36 and
         type(value.get("argv")) is list and value["argv"] and
         all(type(s) is str for s in value["argv"]) and value.get("cpu_affinity") == [12],
         "Measured process identity missing")
