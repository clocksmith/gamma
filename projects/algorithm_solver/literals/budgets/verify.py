"""Execute hash-checked decoded budget packages using the existing Linux judge."""
import argparse
import json
from pathlib import Path
import platform
import sys
import time

from compare import PILOT, digest, json_bytes, decode, load_sources
from verify_execution import load_module, strict_object, HARNESS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sandbox-module", type=Path,
                        default=PILOT.parent / "algsolve/judge/sandbox.py")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    observations = args.output / "observations"
    observations.mkdir()
    sources = load_sources()
    checks_raw = (PILOT / "checks.py").read_bytes()
    checks_pin = json.loads((PILOT / "checks_manifest.json").read_bytes())
    if digest(checks_raw) != checks_pin["checks_sha256"]:
        raise ValueError("checks drift")
    checks = load_module("budget_checks", PILOT / "checks.py", checks_raw)
    sandbox_raw = args.sandbox_module.read_bytes()
    sandbox = load_module("budget_sandbox", args.sandbox_module, sandbox_raw)
    jobs = {}
    manifests = {}
    for folder in sorted(args.packages.glob("budget-*")):
        raw = (folder / "manifest.json").read_bytes()
        manifest = json.loads(raw)
        dictionary = (folder / "dictionary.ltd").read_bytes()
        if digest(dictionary) != manifest["dictionary_sha256"]:
            raise ValueError("dictionary drift")
        manifests[folder.name] = digest(raw)
        for key, row in manifest["programs"].items():
            packet = (folder / "programs" / f"{key}.ltv").read_bytes()
            if digest(packet) != row["packet_sha256"] or packet[4] != manifest["bits_per_selection"]:
                raise ValueError("packet drift")
            source = decode(dictionary, packet)
            if digest(source.encode()) != row["source_sha256"] or source != sources[key][row["arm"]]:
                raise ValueError("source drift")
            identity = (key, row["source_sha256"])
            job = jobs.setdefault(identity, dict(source=source, packages=[]))
            job["packages"].append(dict(name=folder.name, packet_sha256=digest(packet)))
    if not jobs:
        raise ValueError("no complete packages")
    rows = []
    calls = 0
    started = time.perf_counter()
    for (key, source_hash), job in sorted(jobs.items()):
        cases = checks.cases_by_problem[int(key)]
        passed = 0
        failures = []
        for offset in range(0, len(cases), 256):
            selected = cases[offset:offset + 256]
            payload = json_bytes(dict(interface="function", calls=[{"args": c["args"]} for c in selected]))
            result = sandbox.run(
                ["/usr/bin/node", "--jitless", "--single-threaded", "--max-old-space-size=64", "harness.cjs"],
                files={"program.js": job["source"], "inputs.json": payload, "harness.cjs": HARNESS},
                limits=sandbox.Limits(cpu_seconds=3, wall_seconds=8, memory_bytes=1024**3,
                                      max_output_bytes=4 * 1024**2))
            name = f"{key}-{source_hash[:12]}-{offset:05}"
            (observations / (name + ".stdout")).write_bytes(result.stdout)
            (observations / (name + ".stderr")).write_bytes(result.stderr)
            (observations / (name + ".native.json")).write_bytes(json_bytes(dict(
                ok=result.ok, exit_code=result.exit_code, signal=result.signal,
                timed_out=result.timed_out, output_limit_exceeded=result.output_limit_exceeded,
                wall_seconds=result.wall_seconds, notes=result.notes, source_sha256=source_hash,
                input_sha256=digest(payload), stdout_sha256=digest(result.stdout),
                stderr_sha256=digest(result.stderr))))
            calls += 1
            if not result.ok:
                raise RuntimeError("sandbox failure; preserved receipt " + name)
            records = [json.loads(line, object_pairs_hook=strict_object,
                                 parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
                       for line in result.stdout.splitlines()]
            if len(records) != len(selected) + 1 or records[-1] != {"done": len(selected)} \
                    or type(records[-1].get("done")) is not int:
                raise ValueError("completion count")
            for i, record in enumerate(records[:-1]):
                if type(record.get("i")) is not int or record["i"] != i:
                    raise ValueError("output order")
                verdict = checks.check_observation(int(key), offset + i, record)
                passed += bool(verdict["passed"])
                if not verdict["passed"]:
                    failures.append(dict(case=offset + i, verdict=verdict))
        rows.append(dict(problem=key, source_sha256=source_hash, packages=job["packages"],
                         total=len(cases), passed=passed, failures=failures))
    per_package = {}
    for name in manifests:
        matching = [r for r in rows if any(p["name"] == name for p in r["packages"])]
        per_package[name] = dict(programs=len(matching), checks=sum(r["total"] for r in matching),
                                 passed=sum(r["passed"] for r in matching))
    report = dict(schema="gamma.literal-budget-execution.v1",
                  scope="Consumed development checks; identical decoded problem/source pairs executed once",
                  unique_program_sources=len(rows), unique_checks=sum(r["total"] for r in rows),
                  passed_checks=sum(r["passed"] for r in rows), packages=per_package, rows=rows,
                  all_passed=all(r["passed"] == r["total"] for r in rows), sandbox_calls=calls,
                  expected_in_sandbox=False, checks_sha256=digest(checks_raw),
                  sandbox_sha256=digest(sandbox_raw), runner_sha256=digest(Path(__file__).read_bytes()),
                  manifests=manifests, harness_sha256=digest(HARNESS.encode()),
                  codec_sha256=digest((PILOT / "pass2/working/bitpack.py").read_bytes()),
                  platform=platform.platform(), python_version=platform.python_version(),
                  elapsed_seconds=time.perf_counter() - started)
    (args.output / "report.json").write_bytes(json_bytes(report))
    print(json.dumps({k: report[k] for k in
                      ("unique_program_sources", "unique_checks", "passed_checks", "all_passed", "packages")}))
    if not report["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
