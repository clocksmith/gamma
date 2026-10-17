"""Check that each problem's tests accept its own reference solution.

A problem is eligible for sampling only if its reference passes both its
public tests and its hidden tests in the sandbox. This catches parse errors in
imported tests, references that need unavailable modules (sortedcontainers is
not installed in the sandbox interpreter), and limits that are too tight.
Results are cached in data/derived/reference_validation.jsonl.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
from pathlib import Path
from typing import Iterable

from .judge import judge
from .records import DERIVED, Problem, load_hidden_tests

CACHE = DERIVED / "reference_validation.jsonl"


def functional_tests(raw: list[dict]) -> list[judge.FunctionalTest]:
    return [judge.FunctionalTest(args=t["args"], expected=t["expected"], compare=t.get("compare", "return")) for t in raw]


def stdin_tests(raw: list[dict]) -> list[judge.StdinTest]:
    return [judge.StdinTest(input=t["input"], expected=t["expected"]) for t in raw]


def judge_problem(problem: Problem, source: str, raw_tests: list[dict], *, wall_seconds: float = 30.0) -> judge.Verdict:
    if problem.io_mode == "functional":
        tests = functional_tests(raw_tests)
        if problem.slug == 'course-schedule-ii' and problem.entry.get('method') == 'findOrder':
            for test in tests:
                test.validator = 'topological_order'
        return judge.judge_functional(
            source,
            problem.entry,
            tests,
            per_test_cpu_seconds=problem.cpu_seconds,
            wall_seconds=wall_seconds,
            memory_bytes=problem.memory_bytes,
        )
    return judge.judge_stdin(
        source,
        stdin_tests(raw_tests),
        per_test_cpu_seconds=problem.cpu_seconds,
        wall_seconds=wall_seconds,
        memory_bytes=problem.memory_bytes,
        checker_source=problem.checker,
    )


def content_hash(problem: Problem) -> str:
    """Hash of everything validation depends on; a change invalidates the cache."""
    digest = hashlib.sha256()
    for part in (
        problem.reference_solutions[0] if problem.reference_solutions else "",
        json.dumps(problem.public_tests, sort_keys=True),
        json.dumps(load_hidden_tests(problem), sort_keys=True),
        json.dumps([problem.entry, problem.cpu_seconds, problem.memory_bytes, problem.checker], sort_keys=True),
        json.dumps(problem.import_notes.get("unusable")),
        (Path(__file__).parent / "judge" / "harness_functional.py").read_text(encoding="utf-8"),
        (Path(__file__).parent / "judge" / "judge.py").read_text(encoding="utf-8"),
        (Path(__file__).parent / "judge" / "functional_semantics.py").read_text(encoding="utf-8"),
        Path(__file__).read_text(encoding="utf-8"),
    ):
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def validate_one(problem: Problem) -> dict:
    record = {"uid": problem.uid, "eligible": False, "content_hash": content_hash(problem)}
    if "unusable" in problem.import_notes:
        record["reason"] = problem.import_notes["unusable"]
        return record
    if not problem.reference_solutions:
        record["reason"] = "no reference solution"
        return record
    reference = problem.reference_solutions[0]
    hidden = load_hidden_tests(problem)
    hidden_verdict = judge_problem(problem, reference, hidden, wall_seconds=60.0)
    record["hidden"] = {"passed": hidden_verdict.passed, "reason": hidden_verdict.reason,
                        "tests": hidden_verdict.tests_total, "seconds": round(hidden_verdict.wall_seconds, 3)}
    if problem.public_tests:
        public_verdict = judge_problem(problem, reference, problem.public_tests)
        record["public"] = {"passed": public_verdict.passed, "reason": public_verdict.reason,
                            "tests": public_verdict.tests_total}
        if not public_verdict.passed:
            record["public_failure"] = public_verdict.first_failure
    if not hidden_verdict.passed:
        record["reason"] = f"reference fails hidden tests: {hidden_verdict.reason}"
        record["hidden_failure"] = hidden_verdict.first_failure
        record["stderr_tail"] = hidden_verdict.stderr_tail[-300:]
    elif problem.public_tests and not record["public"]["passed"]:
        record["reason"] = "reference fails parsed public examples"
    else:
        record["eligible"] = True
    return record


def load_cache() -> dict[str, dict]:
    if not CACHE.exists():
        return {}
    out = {}
    for line in CACHE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            out[item["uid"]] = item
    return out


def validate(problems: Iterable[Problem], workers: int = 12) -> dict[str, dict]:
    cache = load_cache()
    problems = list(problems)
    todo = [p for p in problems if cache.get(p.uid, {}).get("content_hash") != content_hash(p)]
    if todo:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool, CACHE.open("a", encoding="utf-8") as out:
            for record in pool.map(validate_one, todo):
                cache[record["uid"]] = record
                out.write(json.dumps(record) + "\n")
                out.flush()
    return cache


if __name__ == "__main__":
    import collections
    import sys

    from .records import read_problems

    sources = set(sys.argv[1:]) or {"lcd"}
    selected = [p for p in read_problems(DERIVED / "problems.jsonl") if p.source in sources]
    results = validate(selected)
    counts = collections.Counter(
        "eligible" if results[p.uid]["eligible"] else results[p.uid].get("reason", "?").split(":")[0]
        for p in selected
    )
    print(json.dumps(dict(counts), indent=1))
