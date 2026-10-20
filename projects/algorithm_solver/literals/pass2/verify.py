"""Check new reconstructed rewrites against the unchanged host-only dev oracles."""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from literals import digest, json_bytes, dictionary_bytes, program_bytes, decode_bytes
from verify_execution import load_module, strict_object, HARNESS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sandbox-module", type=Path,
                        default=ROOT.parent.parent / "algsolve/judge/sandbox.py")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((ROOT / "source_manifest.json").read_text())
    checks_raw = (ROOT.parent / "checks.py").read_bytes()
    if digest(checks_raw) != manifest["checks_sha256"]:
        raise ValueError("checks drift")
    baseline_raw = (ROOT.parent / "execution/report.json").read_bytes()
    if digest(baseline_raw) != manifest["baseline_execution_sha256"]:
        raise ValueError("baseline evidence drift")
    baseline = json.loads(baseline_raw)
    if baseline["checks_sha256"] != manifest["checks_sha256"]:
        raise ValueError("baseline used different checks")
    checks = load_module("pass2_checks", ROOT.parent / "checks.py", checks_raw)
    sandbox_raw = args.sandbox_module.read_bytes()
    sandbox = load_module("pass2_sandbox", args.sandbox_module, sandbox_raw)
    witnessed = {}
    for path in sorted((ROOT / "results/encodings").glob("*.json")):
        packet = json.loads(path.read_text())
        dictionary = dictionary_bytes(packet["literals"])
        for key, row in packet["programs"].items():
            variant = packet["selection"]["choices"][key]
            text = decode_bytes(dictionary, program_bytes(packet["literals"], row["sequence"]))
            sha = digest(text.encode())
            if sha != manifest["source_hashes"][f"{key}/{variant}"]:
                raise ValueError("reconstruction differs")
            witnessed[key, variant] = text
    if len(witnessed) != 60:
        raise ValueError("missing source witnesses")
    prior = {(row["problem"], row["source_sha256"]): row for row in baseline["rows"]
             if row["variant"] == "normalized" and row["passed"] == row["total"]}
    for key, variant in witnessed:
        if variant == "baseline":
            row = prior.get((key, manifest["source_hashes"][f"{key}/baseline"]))
            if row is None or type(row["total"]) is not int or row["total"] <= 0:
                raise ValueError("missing passing baseline evidence")
    args.output.mkdir(parents=True, exist_ok=False)
    raw_dir = args.output / "observations"
    raw_dir.mkdir()
    rows = []
    tested = dict(prior)
    total_new = passed_new = calls = 0
    started = time.perf_counter()
    for (key, variant), source in sorted(witnessed.items()):
        if variant == "baseline":
            continue
        sha = digest(source.encode())
        if (key, sha) in tested:
            rows.append({"problem": key, "variant": variant, "source_sha256": sha,
                         "evidence": "identical previously tested source",
                         "total": tested[key, sha]["total"], "passed": tested[key, sha]["passed"]})
            continue
        problem = int(key)
        cases = checks.cases_by_problem[problem]
        total = passed = 0
        failures = []
        for offset in range(0, len(cases), 256):
            selected = cases[offset:offset + 256]
            payload = json_bytes({"interface": "function",
                                  "calls": [{"args": case["args"]} for case in selected]})
            result = sandbox.run(
                ["/usr/bin/node", "--jitless", "--single-threaded", "--max-old-space-size=64", "harness.cjs"],
                files={"program.js": source, "inputs.json": payload, "harness.cjs": HARNESS},
                limits=sandbox.Limits(cpu_seconds=3, wall_seconds=8, memory_bytes=1024 ** 3,
                                      max_output_bytes=4 * 1024 ** 2))
            name = f"{key}-{variant}-{offset:05}"
            (raw_dir / (name + ".stdout")).write_bytes(result.stdout)
            (raw_dir / (name + ".stderr")).write_bytes(result.stderr)
            native = {"exit_code": result.exit_code, "signal": result.signal,
                      "ok": result.ok, "wall_seconds": result.wall_seconds,
                      "timed_out": result.timed_out,
                      "output_limit_exceeded": result.output_limit_exceeded, "notes": result.notes,
                      "source_sha256": sha, "input_sha256": digest(payload),
                      "stdout_sha256": digest(result.stdout), "stderr_sha256": digest(result.stderr)}
            (raw_dir / (name + ".native.json")).write_bytes(json_bytes(native))
            if not result.ok:
                raise RuntimeError("sandbox failure " + name)
            records = [json.loads(line, object_pairs_hook=strict_object,
                                  parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
                       for line in result.stdout.splitlines()]
            if len(records) != len(selected) + 1 or records[-1] != {"done": len(selected)} \
                    or type(records[-1].get("done")) is not int:
                raise ValueError("completion protocol")
            for index, record in enumerate(records[:-1]):
                if type(record.get("i")) is not int or record["i"] != index:
                    raise ValueError("observation order")
                verdict = checks.check_observation(problem, offset + index, record)
                passed += verdict["passed"]
                total += 1
                if not verdict["passed"]:
                    failures.append({"case": offset + index, "verdict": verdict})
            calls += 1
        row = {"problem": key, "variant": variant, "source_sha256": sha,
               "evidence": "new reconstructed source executed", "total": total,
               "passed": passed, "failures": failures}
        tested[key, sha] = row
        rows.append(row)
        total_new += total
        passed_new += passed
    report = {"schema": "gamma.literal-rewrite-execution.v1", "rows": rows,
              "new_source_versions_executed": sum(r["evidence"].startswith("new") for r in rows),
              "new_cases": total_new, "new_passed": passed_new, "sandbox_calls": calls,
              "all_variants_passed": all(r["passed"] == r["total"] for r in rows),
              "all_variants": len(rows), "baseline_execution_sha256": digest(baseline_raw),
              "checks_sha256": digest(checks_raw), "sandbox_sha256": digest(sandbox_raw),
              "runner_sha256": digest(Path(__file__).read_bytes()),
              "harness_sha256": digest(HARNESS.encode() if isinstance(HARNESS, str) else HARNESS),
              "shared_verifier_sha256": digest((ROOT.parent / "verify_execution.py").read_bytes()),
              "expected_in_sandbox": False,
              "elapsed_seconds": time.perf_counter() - started}
    (args.output / "report.json").write_bytes(json_bytes(report))
    print(json.dumps({k: report[k] for k in ("new_source_versions_executed", "new_cases", "new_passed", "all_variants_passed")}))
    if not report["all_variants_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
