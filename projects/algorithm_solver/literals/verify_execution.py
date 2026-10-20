"""Run reconstructed known-program bytes in Gamma's bounded Linux sandbox.

Development checks only. Expected outputs stay in the host oracle module.
No corpus admission, protected evaluation, or autonomous solving claim.
"""
import argparse
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

from literals import decode_bytes, dictionary_bytes, program_bytes, json_bytes, digest
from experiment import IDS, VARIANTS

HARNESS = r"""
"use strict";
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync("program.js", "utf8");
const packet = JSON.parse(fs.readFileSync("inputs.json", "utf8"));
vm.runInThisContext(source, {filename: "program.js", timeout: 1000});
const Target = vm.runInThisContext(packet.interface === "function" ? "solve" : "Solution");
for (let i = 0; i < packet.calls.length; i += 1) {
  const args = packet.calls[i].args;
  const argsBefore = JSON.parse(JSON.stringify(args));
  let record;
  try {
    const result = packet.interface === "function" ? Target(...args) : new Target()[packet.method](...args);
    record = {i, result, args_before: argsBefore, args_after: args};
  } catch (error) {
    record = {i, error: String(error), args_before: argsBefore, args_after: args};
  }
  process.stdout.write(JSON.stringify(record) + "\n");
}
process.stdout.write(JSON.stringify({done: packet.calls.length}) + "\n");
"""


def load_module(name, path, retained=None):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    raw = path.read_bytes() if retained is None else retained
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate output key")
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sandbox-module", type=Path,
                        default=Path(__file__).resolve().parent.parent / "algsolve/judge/sandbox.py")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    checks_path = root / "checks.py"
    frozen_checks = json.loads((root / "checks_manifest.json").read_text())
    checks_raw = checks_path.read_bytes()
    if digest(checks_raw) != frozen_checks["checks_sha256"]:
        raise ValueError("oracle source mismatch")
    checks = load_module("literal_development_checks", checks_path, checks_raw)
    sandbox_raw = args.sandbox_module.read_bytes()
    sandbox = load_module("literal_sandbox", args.sandbox_module, sandbox_raw)
    frozen_sources = json.loads((root / "source_manifest.json").read_text())["source_hashes"]
    # Decode actual saved sequences. Every source version must have at least one
    # complete decoded witness; no executing a source file instead of its witness.
    witnessed = {}
    reconstructions = 0
    for path in sorted((root / "results/encodings").glob("*.json")):
        packet = json.loads(path.read_text())
        dictionary = dictionary_bytes(packet["literals"])
        for key, row in packet["programs"].items():
            text = decode_bytes(dictionary, program_bytes(packet["literals"], row["sequence"]))
            variant = packet["selection"]["choices"][key]
            source_key = f"{key}/{variant}"
            if digest(text.encode()) != frozen_sources[source_key] or row["source_sha256"] != frozen_sources[source_key]:
                raise ValueError("decoded source mismatch")
            witnessed[source_key] = text
            reconstructions += 1
    if set(witnessed) != set(frozen_sources):
        raise ValueError("missing reconstructed source variant")
    args.output.mkdir(parents=True, exist_ok=False)
    raw_dir = args.output / "observations"
    raw_dir.mkdir()
    limits = sandbox.Limits(cpu_seconds=3, wall_seconds=8, memory_bytes=1024 ** 3,
                            max_output_bytes=4 * 1024 ** 2)
    # A dedicated, explicit pilot contract: up to256 bounded development inputs
    # per call, independent of the campaign's four-case qualification contract.
    chunk_size = 256
    rows = []
    started = time.perf_counter()
    for key in IDS:
        problem = int(key)
        cases = checks.cases_by_problem[problem]
        for variant in VARIANTS:
            source_key = f"{key}/{variant}"
            source = witnessed[source_key]
            passed = 0
            mutations = 0
            failures = []
            calls = []
            for offset in range(0, len(cases), chunk_size):
                selected = cases[offset:offset + chunk_size]
                packet = {"interface": "function" if variant == "normalized" else "solution-class",
                          "method": checks.METHODS[problem],
                          "calls": [{"args": case["args"]} for case in selected]}
                payload = json_bytes(packet)
                result = sandbox.run(
                    ["/usr/bin/node", "--jitless", "--single-threaded", "--max-old-space-size=64", "harness.cjs"],
                    files={"program.js": source, "inputs.json": payload, "harness.cjs": HARNESS},
                    limits=limits,
                )
                name = f"{key}-{variant}-{offset:05}"
                (raw_dir / f"{name}.stdout").write_bytes(result.stdout)
                (raw_dir / f"{name}.stderr").write_bytes(result.stderr)
                native = {"exit_code": result.exit_code, "signal": result.signal,
                          "timed_out": result.timed_out, "output_limit_exceeded": result.output_limit_exceeded,
                          "notes": result.notes, "wall_seconds": result.wall_seconds,
                          "source_sha256": frozen_sources[source_key], "input_only_sha256": digest(payload),
                          "stdout_sha256": digest(result.stdout), "stderr_sha256": digest(result.stderr)}
                (raw_dir / f"{name}.native.json").write_bytes(json_bytes(native))
                calls.append(native)
                if not result.ok:
                    raise RuntimeError(f"native sandbox failure: {name}: {native}")
                records = [json.loads(line, object_pairs_hook=strict_object,
                                     parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
                           for line in result.stdout.splitlines()]
                if len(records) != len(selected) + 1 or records[-1] != {"done": len(selected)} \
                        or type(records[-1].get("done")) is not int:
                    raise ValueError("output completion/count")
                for index, observation in enumerate(records[:-1]):
                    if type(observation.get("i")) is not int or observation["i"] != index:
                        raise ValueError("output order")
                    verdict = checks.check_observation(problem, offset + index, observation)
                    passed += bool(verdict["passed"])
                    mutations += not verdict["input_preserved"]
                    if not verdict["passed"]:
                        failures.append({"case": offset + index, "verdict": verdict})
            rows.append({"problem": key, "variant": variant, "total": len(cases), "passed": passed,
                         "mutation_failures": mutations, "failures": failures, "sandbox_calls": len(calls),
                         "source_sha256": frozen_sources[source_key]})
    report = {"schema": "gamma.literal-pilot-execution.v1",
              "scope": "known-program development tests; no protected or autonomous evaluation",
              "exact_reconstructions_checked": reconstructions,
              "unique_source_versions_executed": len(rows),
              "total_cases": sum(row["total"] for row in rows),
              "passed_cases": sum(row["passed"] for row in rows),
              "source_versions_all_cases_passed": sum(row["passed"] == row["total"] for row in rows),
              "sandbox_calls": sum(row["sandbox_calls"] for row in rows), "rows": rows,
              "expected_outputs_in_sandbox": False,
              "checks_sha256": digest(checks_raw),
              "sandbox_sha256": digest(sandbox_raw),
              "runner_sha256": digest(Path(__file__).read_bytes()),
              "node_sha256": digest(Path("/usr/bin/node").read_bytes()),
              "node_version": subprocess.check_output(["/usr/bin/node", "--version"], text=True).strip(),
              "python_version": platform.python_version(), "platform": platform.platform(),
              "elapsed_seconds": time.perf_counter() - started,
              "limits": {"cpu_seconds_per_call": 3, "wall_seconds_per_call": 8,
                         "memory_bytes_per_call": 1024 ** 3, "max_cases_per_call": chunk_size}}
    (args.output / "report.json").write_bytes(json_bytes(report))
    print(json.dumps({k: report[k] for k in ("total_cases", "passed_cases",
                     "source_versions_all_cases_passed", "sandbox_calls", "elapsed_seconds")}))
    if report["total_cases"] != report["passed_cases"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
