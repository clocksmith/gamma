"""Fresh, fail-closed qualification; expectations never enter candidate sandboxes."""
from __future__ import annotations

import argparse
import copy
import hashlib
import heapq
import json
from pathlib import Path
import random
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent))
from variants import METHODS, build_sources, provenance
from algsolve.judge import sandbox

SEED = 20261024
SCHEMA = "gamma.readable-joint-blocks.qualification.v1"

PYTHON_RUNNER = '''import json, sys
packet = json.load(sys.stdin)
namespace = {}
exec(compile(open("program.py").read(), "program.py", "exec"), namespace)
for index, call in enumerate(packet["calls"]):
    args = call["args"]
    for target, origin in call.get("alias_rows", []):
        args[0][target] = args[0][origin]
    outer = args[0]
    rows = list(outer)
    before = json.loads(json.dumps(args))
    try:
        result = getattr(namespace["Solution"](), packet["method"])(*args)
        kind = "boolean" if type(result) is bool else "number" if type(result) is int else type(result).__name__
        record = {"i": index, "result": result, "result_type": kind}
    except Exception as error:
        record = {"i": index, "error": type(error).__name__ + ": " + str(error)}
    record.update(args_before=before, args_after=args, identities_preserved=(args[0] is outer and len(outer) == len(rows) and all(a is b for a,b in zip(outer, rows))))
    print(json.dumps(record, separators=(",", ":")))
print(json.dumps({"done": len(packet["calls"])}))
'''

JAVASCRIPT_RUNNER = '''"use strict";
const fs = require("fs"), vm = require("vm");
const packet = JSON.parse(fs.readFileSync(0, "utf8"));
vm.runInThisContext(fs.readFileSync("program.js", "utf8"), {timeout:1000});
const Constructor = vm.runInThisContext("Solution");
for (let index = 0; index < packet.calls.length; index += 1) {
  const call = packet.calls[index], args = call.args;
  for (const [target, origin] of (call.alias_rows || [])) args[0][target] = args[0][origin];
  const outer = args[0], rows = outer.slice(), before = JSON.parse(JSON.stringify(args));
  let record;
  try {
    const result = new Constructor()[packet.method](...args);
    record = {i:index, result:result, result_type:typeof result};
  } catch (error) { record = {i:index, error:String(error)}; }
  record.args_before = before; record.args_after = args;
  record.identities_preserved = args[0] === outer && outer.length === rows.length && rows.every((row,i) => outer[i] === row);
  process.stdout.write(JSON.stringify(record) + "\\n");
}
process.stdout.write(JSON.stringify({done:packet.calls.length}) + "\\n");
'''


def json_bytes(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def component_oracle(matrix):
    parent = list(range(len(matrix)))
    def find(node):
        while parent[node] != node:
            node = parent[node]
        return node
    for left in range(len(matrix)):
        for right in range(left):
            if matrix[left][right]:
                parent[find(left)] = find(right)
    return len({find(node) for node in range(len(matrix))})


def rooms_oracle(rooms):
    reached = {0}
    while True:
        expanded = reached | {key for room in reached for key in rooms[room]}
        if expanded == reached:
            return len(reached) == len(rooms)
        reached = expanded


def grid_oracle(grid):
    size = len(grid)
    if grid[0][0] or grid[-1][-1]:
        return -1
    distances = {(0, 0): 1}
    pending = [(1, 0, 0)]
    while pending:
        distance, row, column = heapq.heappop(pending)
        if distance != distances[row, column]:
            continue
        if (row, column) == (size - 1, size - 1):
            return distance
        for dr, dc in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
            other = row + dr, column + dc
            if 0 <= other[0] < size and 0 <= other[1] < size and not grid[other[0]][other[1]]:
                if distance + 1 < distances.get(other, size * size + 1):
                    distances[other] = distance + 1
                    heapq.heappush(pending, (distance + 1, *other))
    return -1


ORACLES = {"547": component_oracle, "841": rooms_oracle, "1091": grid_oracle}


def materialized_args(case):
    args = copy.deepcopy(case["args"])
    for target, origin in case.get("alias_rows", []):
        args[0][target] = args[0][origin]
    return args


def build_cases():
    """Only new synthetic cases and the seven public samples, never private tests."""
    cases = {problem: [] for problem in METHODS}
    def add(problem, value, category, aliases=None, compatibility_only=False):
        case = {"args": [value], "category": category, "expectation_mode": "predecessor-effect-compatibility" if compatibility_only else "independent-oracle"}
        if aliases:
            case["alias_rows"] = aliases
        if not compatibility_only:
            case["expected"] = ORACLES[problem](materialized_args(case)[0])
        cases[problem].append(case)
    for size in range(1, 6):
        edges = [(i,j) for i in range(size) for j in range(i)]
        for mask in range(1 << len(edges)):
            matrix = [[int(i == j) for j in range(size)] for i in range(size)]
            for bit, (i,j) in enumerate(edges):
                matrix[i][j] = matrix[j][i] = (mask >> bit) & 1
            add("547", matrix, "exhaustive-symmetric-small")
    for size in range(1, 4):
        for mask in range(1 << (size * size)):
            add("841", [[j for j in range(size) if mask & (1 << (i*size+j))] for i in range(size)], "exhaustive-directed-small")
            add("1091", [[(mask >> (i*size+j)) & 1 for j in range(size)] for i in range(size)], "exhaustive-binary-small")
    rng = random.Random(SEED)
    for _ in range(48):
        size = rng.randrange(4, 17)
        matrix = [[int(i == j) for j in range(size)] for i in range(size)]
        for i in range(size):
            for j in range(i):
                matrix[i][j] = matrix[j][i] = int(rng.random() < .2)
        add("547", matrix, "seeded-larger")
        add("841", [[j for j in range(size) if rng.random() < .2] for i in range(size)], "seeded-larger")
        add("1091", [[int(rng.random() < .3) for j in range(size)] for i in range(size)], "seeded-larger")
    add("547", [[1] * 200 for _ in range(200)], "declared-bound-dense")
    add("547", [[int(i == j) for j in range(200)] for i in range(200)], "declared-bound-disconnected")
    add("841", [[i+1] if i < 999 else [] for i in range(1000)], "declared-bound-chain")
    add("841", [[] for _ in range(1000)], "declared-bound-unreachable")
    add("841", [[0,1,1],[1,2,2],[2]], "duplicate-self-edges")
    for value in (0, 1):
        add("1091", [[value] * 100 for _ in range(100)], "declared-bound-uniform")
    add("547", [[1,1],[1,1]], "shared-row-identity", [[1,0]])
    add("841", [[1],[1]], "shared-row-identity", [[1,0]])
    # Shared rows are outside the ordinary independent-cell grid domain. Input
    # mutation makes the nonmutating graph-distance oracle inapplicable here.
    # Retain this as explicit predecessor compatibility, not oracle correctness.
    add("1091", [[0,0],[0,0]], "shared-row-identity", [[1,0]], compatibility_only=True)
    for problem in METHODS:
        fixtures = json.loads((HERE.parent / "readable-v1" / "fixtures" / f"{problem}.json").read_text())
        for fixture in fixtures:
            assert ORACLES[problem](fixture["args"][0]) == fixture["expected"]
            add(problem, fixture["args"][0], "public-sample")
    return cases


def exact(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        return len(left) == len(right) and all(exact(a,b) for a,b in zip(left,right))
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(exact(left[key], right[key]) for key in left)
    return left == right


def judge_record(problem, case, record, original=None):
    before = materialized_args(case)
    compatibility_only = case.get("expectation_mode") == "predecessor-effect-compatibility"
    kind = "boolean" if problem == "841" else "number"
    value_type = bool if problem == "841" else int
    if record.get("error") or record.get("result_type") != kind or type(record.get("result")) is not value_type:
        return False
    if not compatibility_only and not exact(record.get("result"), case["expected"]):
        return False
    if record.get("identities_preserved") is not True or not exact(record.get("args_before"), before):
        return False
    after = record.get("args_after")
    if problem != "1091":
        if not exact(after, before):
            return False
    else:
        if not isinstance(after, list) or len(after) != 1 or not isinstance(after[0], list) or len(after[0]) != len(before[0]):
            return False
        for old_row, new_row in zip(before[0], after[0]):
            if not isinstance(new_row, list) or len(old_row) != len(new_row):
                return False
            if any(type(b) is not int or b not in (a, 1) for a,b in zip(old_row,new_row)):
                return False
    return original is None or (exact(after, original["args_after"]) and exact(record["result"], original["result"]))


def payload(method, cases):
    return {"method": method, "calls": [{key: case[key] for key in ("args", "alias_rows") if key in case} for case in cases]}


def parse_records(raw, count):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("nonfinite JSON value: " + value)
    rows = [json.loads(line, object_pairs_hook=pairs, parse_constant=invalid) for line in raw.splitlines()]
    if len(rows) != count + 1 or not all(isinstance(row,dict) for row in rows) or rows[-1] != {"done": count} or type(rows[-1].get("done")) is not int:
        raise ValueError("incomplete candidate output")
    if any(type(row.get("i")) is not int or row["i"] != index for index,row in enumerate(rows[:-1])):
        raise ValueError("candidate output index mismatch")
    return rows[:-1]


def qualify(output: Path, languages: tuple[str, ...] = ("python", "javascript"), node_runtime: Path | None = None):
    if not languages or len(set(languages)) != len(languages) or any(x not in ("python", "javascript") for x in languages):
        raise ValueError("select distinct supported languages")
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    cases = build_cases()
    sources = {language: problems for language, problems in build_sources().items() if language in languages}
    source_rows = [row for row in provenance() if row["language"] in languages]
    rows = [{**row, "passed": False, "checks_total": len(cases[row["problem_id"]]), "checks_passed": 0,
             "independent_oracle_checks_total": sum(case["expectation_mode"] == "independent-oracle" for case in cases[row["problem_id"]]),
             "predecessor_compatibility_checks_total": sum(case["expectation_mode"] == "predecessor-effect-compatibility" for case in cases[row["problem_id"]])} for row in source_rows]
    code = {name: sha((HERE/name).read_bytes()) for name in ("variants.py", "qualify.py", "QUALIFICATION.md")}
    contract = {"schema": SCHEMA, "seed": SEED, "sources": source_rows, "cases_sha256": sha(json_bytes(cases)), "code_sha256": code,
                "cases_by_problem": {p:len(c) for p,c in cases.items()}, "case_origin": "synthetic_and_public_samples_only", "max_total_wall_seconds": 180,
                "batch_cases": 128, "sandbox": "existing_algsolve.judge.sandbox.run_unmodified", "sandbox_sha256": sha(Path(sandbox.__file__).read_bytes()),
                "runtime_paths": {"python": "/usr/bin/python3", "javascript": "/usr/bin/node"}, "protected_access": False}
    if set(languages) != {"python", "javascript"}:
        contract['language_scope'] = list(languages)
        contract['runtime_paths'] = {key: value for key, value in contract['runtime_paths'].items() if key in languages}
        contract['scope'] = 'language-only prerequisite; not paired qualification or M1'
    runtime_manifest = None
    if node_runtime is not None:
        from algsolve.judge import pinned_runtime
        runtime_manifest = pinned_runtime.freeze_runtime(node_runtime)
        contract['runtime_identity'] = runtime_manifest
        contract['runtime_paths']['javascript'] = '/runtime/node'
        contract['runtime_adapter_sha256'] = sha(Path(pinned_runtime.__file__).read_bytes())
    raw = json_bytes(contract)
    (output/"contract.json").write_bytes(raw)
    report = {"schema": SCHEMA, "status": "blocked", "success": False, "rows": rows, "cases_sha256": contract["cases_sha256"], "code_sha256": code,
              "qualification_contract_sha256": sha(raw), "failures": [], "candidate_executions": 0, "protected_access": False}
    try:
        missing = [path for path in contract["runtime_paths"].values() if path != "/runtime/node" and not Path(path).is_file()]
        if missing:
            raise sandbox.SandboxUnavailable("Required runtime absent from existing sandbox mount: " + ", ".join(missing))
        for language, problems in sources.items():
            for problem, versions in problems.items():
                original = []
                for variant, source in versions.items():
                    row = next(r for r in rows if (r["language"],r["problem_id"],r["variant"]) == (language,problem,variant))
                    observations = []
                    for offset in range(0, len(cases[problem]), contract["batch_cases"]):
                        if time.monotonic() - started > contract["max_total_wall_seconds"]:
                            raise TimeoutError("total qualification wall budget exceeded")
                        batch = cases[problem][offset:offset+contract["batch_cases"]]
                        if language == "python":
                            argv = ["/usr/bin/python3", "-I", "-S", "runner.py"]
                            files = {"program.py": source, "runner.py": PYTHON_RUNNER}
                        else:
                            argv = ["/usr/bin/node", "--jitless", "--single-threaded", "--max-old-space-size=64", "runner.cjs"]
                            files = {"program.js": source, "runner.cjs": JAVASCRIPT_RUNNER}
                        limits = sandbox.Limits(cpu_seconds=4,wall_seconds=10,memory_bytes=1024**3,max_output_bytes=8*1024**2)
                        if language == 'javascript' and runtime_manifest is not None:
                            result = pinned_runtime.run_node(node_runtime, manifest=runtime_manifest, files=files,
                                stdin=json_bytes(payload(METHODS[problem],batch)), limits=limits, node_args=argv[1:])
                        else:
                            result = sandbox.run(argv, files=files, stdin=json_bytes(payload(METHODS[problem],batch)), limits=limits)
                        report["candidate_executions"] += 1
                        stem = f"{language}-{problem}-{variant}-{offset}"
                        (output/(stem+".stdout")).write_bytes(result.stdout)
                        (output/(stem+".stderr")).write_bytes(result.stderr)
                        if not result.ok:
                            raise RuntimeError("candidate process failed: " + stem)
                        records = parse_records(result.stdout, len(batch))
                        observations.extend(records)
                        for index, (case, record) in enumerate(zip(batch,records)):
                            baseline = None if variant == "original" else original[offset+index]
                            valid = judge_record(problem,case,record,baseline)
                            row["checks_passed"] += int(valid)
                            if not valid:
                                report["failures"].append({"source": {k:row[k] for k in ("language","problem_id","variant","sha256")}, "case_index": offset+index, "case": case, "record": record})
                    row["passed"] = row["checks_passed"] == row["checks_total"]
                    if variant == "original":
                        if not row["passed"]:
                            raise RuntimeError("predecessor failed fresh independent/effect checks")
                        original = observations
        report["success"] = all(row["passed"] for row in rows) and not report["failures"]
        report["status"] = "passed" if report["success"] else "failed"
    except sandbox.SandboxUnavailable as error:
        report["blocker"] = str(error)
    except Exception as error:
        report["status"] = "failed"
        report["blocker"] = type(error).__name__ + ": " + str(error)
    report["elapsed_seconds"] = time.monotonic() - started
    (output/"qualification.json").write_bytes(json_bytes(report))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--language", choices=("python", "javascript"), action="append")
    parser.add_argument("--node-runtime", type=Path)
    arguments = parser.parse_args()
    receipt = qualify(arguments.output, tuple(arguments.language) if arguments.language else ("python", "javascript"), arguments.node_runtime)
    print(json.dumps({key:receipt[key] for key in ("status","success","candidate_executions")}, sort_keys=True))
    if "blocker" in receipt:
        print(receipt["blocker"])
    raise SystemExit(0 if receipt["success"] else 2)
