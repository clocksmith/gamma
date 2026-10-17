"""One command for the bounded four-route comparison.

    python -m algsolve.run --run-name baseline-v1

Preconditions (fail closed): the sample manifest is committed and unchanged,
its hash matches contracts/run_contract.json, the GPU compute probe passes,
and a quick judge self-check rejects forged, hanging and networked candidates.

Stages (each resumable; finished items are skipped on rerun):
  fit          paraphrases for recognition queries, lookup thresholds on the
               dev queries, pattern classifier; frozen to contracts/
  recognition  lookup on the 200 recognition queries; returned solutions are
               judged on the true problem's hidden tests
  solving      the four routes on the 150 solving problems; final candidates
               (and first attempts) judged on public and hidden tests
  report       rebuilt from the results files only (see report.py)
"""

from __future__ import annotations

import argparse
import json
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path

from . import paraphrase, report, splits, validate
from .judge import judge
from .records import LANE_ROOT, Problem, load_hidden_tests

CONTRACT_PATH = LANE_ROOT / "contracts" / "run_contract.json"
RUNS = LANE_ROOT / "runs"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=LANE_ROOT, capture_output=True, text=True, check=False).stdout.strip()


def check_manifest_committed(contract: dict) -> str:
    relative = splits.MANIFEST_PATH.relative_to(Path(git("rev-parse", "--show-toplevel")))
    if not git("ls-files", str(relative)):
        raise SystemExit("sample manifest is not committed; commit it before any model run")
    if git("status", "--porcelain", str(relative)):
        raise SystemExit("sample manifest has uncommitted changes")
    digest = splits.manifest_sha256()
    if digest != contract["sample"]["manifest_sha256"]:
        raise SystemExit(f"manifest sha256 {digest} != contract {contract['sample']['manifest_sha256']}")
    return digest


def gpu_probe() -> dict:
    import torch

    info = {"torch": torch.__version__, "hip": torch.version.hip, "cuda_available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count()}
    if not torch.cuda.is_available():
        raise SystemExit(f"GPU not available: {info}")
    a = torch.randn(256, 256, device="cuda")
    value = float((a @ a).sum().item())
    torch.cuda.synchronize()
    info.update(device=torch.cuda.get_device_name(0), matmul_probe="ok", probe_value_finite=value == value)
    return info


def judge_selfcheck() -> dict:
    entry = {"class": "Solution", "method": "f"}
    tests = [judge.FunctionalTest(args=[1], expected=2)]
    good = "class Solution:\n    def f(self, x):\n        return x + 1\n"
    hang = "class Solution:\n    def f(self, x):\n        while True:\n            pass\n"
    net = ("class Solution:\n    def f(self, x):\n        import socket\n        try:\n"
           "            socket.create_connection(('1.1.1.1', 53), timeout=2)\n            return 2\n"
           "        except OSError:\n            return 0\n")
    checks = {
        "correct_passes": judge.judge_functional(good, entry, tests, wall_seconds=8).passed,
        "zero_tests_fail": not judge.judge_functional(good, entry, [], wall_seconds=8).passed,
        "hang_fails": not judge.judge_functional(hang, entry, tests, per_test_cpu_seconds=1, wall_seconds=5).passed,
        "network_blocked": not judge.judge_functional(net, entry, tests, wall_seconds=8).passed,
    }
    required = ("correct_passes", "zero_tests_fail", "hang_fails", "network_blocked")
    if not all(checks[k] for k in required):
        raise SystemExit(f"judge self-check failed: {checks}")
    return checks


def contract_line(run_name: str, contract: dict, digest: str) -> str:
    model = contract["model"]
    return (
        f"[run-contract] run_name={run_name} pairs_input_spec=contracts/sample_manifest.json@{digest[:12]} "
        f"resume_from=none resume_stage=none decode={model['decoding']} "
        f"eval_dataset_paths=data/derived/problems.jsonl,data/derived/tests device=cuda schedule=none "
        f"runtime_mode=normal_rocm sweep_mode=live model={model['repo']}@{model['revision'][:12]} "
        f"thinking={model['thinking']} route_wall_seconds={contract['budgets']['route_wall_seconds']} "
        f"first_max_new_tokens={contract['budgets']['first_attempt_max_new_tokens']} "
        f"repair_max_new_tokens={contract['budgets']['repair_max_new_tokens']} repairs={contract['budgets']['repairs']}"
    )


def load_done(path: Path, key) -> set:
    if not path.exists():
        return set()
    return {key(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


# --- stages ------------------------------------------------------------------

def stage_fit(generator, embedder, entries, problems, manifest) -> None:
    from . import classify
    from .lookup import THRESHOLDS_PATH, LookupIndex, fit_thresholds

    by_key = {e.key: e for e in entries}
    wanted = sorted({q["target"] for q in manifest["recognition"] + manifest["recognition_dev"]
                     if q["kind"] in ("paraphrase", "sibling_paraphrase")})
    paraphrases = paraphrase.generate(generator, [by_key[k] for k in wanted])
    if not THRESHOLDS_PATH.exists():
        lookup = LookupIndex.load(entries)
        cases = []
        for query in manifest["recognition_dev"]:
            text = recognition_query_text(query, by_key, problems, paraphrases)
            vector = embedder.encode([text], query=True)[0]
            cases.append((lookup.scored_candidates(text, vector), query["target"]))
        thresholds = fit_thresholds(cases)
        thresholds["fitted_on"] = "recognition_dev queries only"
        THRESHOLDS_PATH.write_text(json.dumps(thresholds, indent=1) + "\n")
    if not classify.MODEL_PATH.exists():
        classify.train(entries)


def recognition_query_text(query: dict, by_key: dict, problems: dict, paraphrases: dict) -> str:
    if query["kind"] == "exact":
        return by_key[query["target"]].query_text()
    if query["kind"] in ("paraphrase", "sibling_paraphrase"):
        entry = by_key[query["target"]]
        return paraphrase.query_text(entry, paraphrases[entry.key]["paraphrase"])
    if query["kind"] == "absent_exact":
        return problems[query["problem_uid"]].query_text()
    raise ValueError(query["kind"])


def score_code(problem: Problem, code: str | None) -> dict:
    """Final scoring outside the route: public examples and hidden tests."""
    if not code:
        return {"public": None, "hidden": None, "evidence": "failed", "judge_seconds": 0.0}
    started = time.perf_counter()
    public = validate.judge_problem(problem, code, problem.public_tests)
    hidden_tests = load_hidden_tests(problem)
    hidden = validate.judge_problem(problem, code, hidden_tests, wall_seconds=120.0) if hidden_tests else None
    evidence = "failed"
    if public.passed:
        evidence = "example_passed"
        if problem.evidence_ceiling == "independent_tests_passed" and hidden is not None and hidden.passed:
            evidence = "independent_tests_passed"
    return {
        "public": public.to_dict(),
        "hidden": hidden.to_dict() if hidden else None,
        "evidence": evidence,
        "evidence_ceiling": problem.evidence_ceiling,
        "judge_seconds": round(time.perf_counter() - started, 3),
    }


def stage_recognition(run_dir: Path, context, entries, problems, manifest, paraphrases) -> None:
    from .lookup import adapt_solution, fingerprint

    out_path = run_dir / "recognition.jsonl"
    done = load_done(out_path, lambda r: r["qid"])
    by_key = {e.key: e for e in entries}
    with out_path.open("a", encoding="utf-8") as out:
        for query in manifest["recognition"]:
            if query["qid"] in done:
                continue
            text = recognition_query_text(query, by_key, problems, paraphrases)
            started = time.perf_counter()
            vector = context.embedder.encode([text], query=True)[0]
            match = context.lookup.match(text, vector, context.thresholds)
            lookup_seconds = time.perf_counter() - started
            if query["kind"] == "absent_exact":
                truth_problem = problems[query["problem_uid"]]
            else:
                truth_problem = problems[by_key[query["target"]].judge_uid]
            record = {
                "qid": query["qid"], "group": query["group"], "kind": query["kind"], "target": query["target"],
                "decision": match.decision, "matched": match.key, "score": round(match.score, 4),
                "runner_up": match.runner_up_key, "runner_up_score": round(match.runner_up_score, 4),
                "candidates": [{k: c[k] for k in ("key", "cosine", "score")} for c in match.candidates],
                "lookup_seconds": round(lookup_seconds, 4),
            }
            if query["kind"] in ("paraphrase", "sibling_paraphrase"):
                record["paraphrase_numbers_preserved"] = paraphrases[query["target"]]["numbers_preserved"]
            if match.decision == "match":
                entry = by_key[match.key]
                code = adapt_solution(entry.references[0]["code"], entry, fingerprint(text).method or None)
                record["solution_score"] = score_code(truth_problem, code)
            out.write(json.dumps(record) + "\n")
            out.flush()


def stage_solving(run_dir: Path, context, problems, manifest) -> None:
    from .routes import ROUTES, run_route

    out_path = run_dir / "solving.jsonl"
    done = load_done(out_path, lambda r: (r["uid"], r["route"]))
    uids = manifest["solving"]["lcd"] + manifest["solving"]["lcb"] + manifest["solving"]["cf"]
    total = len(uids) * len(ROUTES)
    with out_path.open("a", encoding="utf-8") as out:
        for n, uid in enumerate(uids):
            problem = problems[uid]
            for route in ROUTES:
                if (uid, route) in done:
                    continue
                result = run_route(context, problem, route)
                record = result.to_dict()
                record["source"] = problem.source
                record["io_mode"] = problem.io_mode
                record["final"] = score_code(problem, result.code)
                generative = [a for a in result.attempts if a.get("stage") in ("first", "repair")]
                if generative and generative[0].get("code"):
                    record["first_attempt"] = score_code(problem, generative[0]["code"])
                record["time_to_checked_answer"] = round(result.seconds + record["final"]["judge_seconds"], 3)
                out.write(json.dumps(record) + "\n")
                out.flush()
                done.add((uid, route))
                print(f"[solving] {len(done)}/{total} {uid} {route} {record['final']['evidence']} "
                      f"{result.seconds:.1f}s", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--stages", default="fit,recognition,solving,report")
    args = parser.parse_args(argv)
    stages = args.stages.split(",")

    contract = json.loads(CONTRACT_PATH.read_text())
    digest = check_manifest_committed(contract)
    run_dir = RUNS / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    if stages == ["report"]:
        report.build(run_dir)
        return 0

    probe = gpu_probe()
    selfcheck = judge_selfcheck()
    line = contract_line(args.run_name, contract, digest)
    print(line, flush=True)
    meta_path = run_dir / "run_meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {"sessions": []}
    meta.update(run_name=args.run_name, contract=contract, manifest_sha256=digest, contract_line=line)
    meta["sessions"].append({
        "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "stages": stages, "gpu_probe": probe,
        "judge_selfcheck": selfcheck, "git_commit": git("rev-parse", "HEAD"),
        "python": sys.version.split()[0], "platform": platform.platform(),
    })
    meta_path.write_text(json.dumps(meta, indent=1) + "\n")

    from .classify import Classifier
    from .embed import Embedder
    from .lookup import LookupIndex, load_thresholds
    from .model import Generator
    from .routes import Budget, Context

    manifest = splits.load_manifest()
    problems = splits.load_all()
    entries = splits.read_index_entries()
    generator = Generator()
    embedder = Embedder()

    if "fit" in stages:
        stage_fit(generator, embedder, entries, problems, manifest)
    paraphrases = paraphrase.generate(generator, []) if paraphrase.PARAPHRASES_PATH.exists() else {}
    context = Context(
        generator=generator, embedder=embedder, lookup=LookupIndex.load(entries), thresholds=load_thresholds(),
        classifier=Classifier(), entries=entries, budget=Budget.from_contract(contract),
    )
    if "recognition" in stages:
        stage_recognition(run_dir, context, entries, problems, manifest, paraphrases)
    if "solving" in stages:
        stage_solving(run_dir, context, problems, manifest)
    meta = json.loads(meta_path.read_text())
    meta["sessions"][-1].update(finished=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                host_max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
    meta_path.write_text(json.dumps(meta, indent=1) + "\n")
    if "report" in stages:
        report.build(run_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
