"""Host-side judging. Expected values stay on the host; verdicts fail closed.

A candidate passes a test set only when the set is non-empty, every test
produced exactly one well-formed record, the harness reported completion, the
sandbox exited cleanly within limits, and every observed value matches the
expected value under the declared comparison.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from . import sandbox

HARNESS_PATH = Path(__file__).with_name("harness_functional.py")
FLOAT_REL_TOL = 1e-5
FLOAT_ABS_TOL = 1e-5

# Failure reasons, in the order a reader should look at them.
NO_TESTS = "no_tests"
SANDBOX_ERROR = "sandbox_error"
LOAD_ERROR = "load_error"
TIMEOUT = "timeout"
OUTPUT_LIMIT = "output_limit"
MALFORMED_OUTPUT = "malformed_output"
DUPLICATE_RESULT = "duplicate_result"
MISSING_RESULT = "missing_result"
INCOMPLETE = "incomplete"
RUNTIME_ERROR = "runtime_error"
WRONG_ANSWER = "wrong_answer"
CHECKER_ERROR = "checker_error"


@dataclass
class FunctionalTest:
    args: list[Any] = field(default_factory=list)
    kwargs: dict[str, Any] = field(default_factory=dict)
    expected: Any = None
    # "return": compare the return value; "arg:<k>": compare positional arg k
    # after the call (in-place problems).
    compare: str = "return"


@dataclass
class StdinTest:
    input: str
    expected: str


@dataclass
class Verdict:
    passed: bool
    reason: str | None
    tests_total: int
    tests_passed: int
    wall_seconds: float
    first_failure: dict | None = None
    stderr_tail: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def values_equal(expected: Any, observed: Any) -> bool:
    if isinstance(expected, bool) or isinstance(observed, bool):
        return type(expected) is type(observed) and expected == observed
    if isinstance(expected, (int, float)) and isinstance(observed, (int, float)):
        if isinstance(expected, int) and isinstance(observed, int):
            return expected == observed
        return math.isclose(float(expected), float(observed), rel_tol=FLOAT_REL_TOL, abs_tol=FLOAT_ABS_TOL)
    if isinstance(expected, list) and isinstance(observed, list):
        return len(expected) == len(observed) and all(values_equal(e, o) for e, o in zip(expected, observed))
    if isinstance(expected, dict) and isinstance(observed, dict):
        return expected.keys() == observed.keys() and all(values_equal(expected[k], observed[k]) for k in expected)
    return expected == observed


def _tail(data: bytes, limit: int = 600) -> str:
    return data[-limit:].decode("utf-8", "replace")


def judge_functional(
    candidate_source: str,
    entry: dict,
    tests: list[FunctionalTest],
    *,
    per_test_cpu_seconds: float = 2.0,
    wall_seconds: float = 30.0,
    memory_bytes: int = 512 * 1024 * 1024,
) -> Verdict:
    if not tests:
        return Verdict(False, NO_TESTS, 0, 0, 0.0)
    calls = {"entry": entry, "calls": [{"args": t.args, "kwargs": t.kwargs} for t in tests]}
    limits = sandbox.Limits(
        cpu_seconds=max(1, math.ceil(per_test_cpu_seconds * len(tests))),
        wall_seconds=wall_seconds,
        memory_bytes=memory_bytes,
    )
    try:
        result = sandbox.run_python(
            "harness.py",
            files={
                "harness.py": HARNESS_PATH.read_text(encoding="utf-8"),
                "candidate.py": candidate_source,
                "calls.json": json.dumps(calls),
            },
            limits=limits,
        )
    except sandbox.SandboxUnavailable as exc:
        return Verdict(False, SANDBOX_ERROR, len(tests), 0, 0.0, {"detail": str(exc)})
    return _score_functional(result, tests)


def _score_functional(result: sandbox.SandboxResult, tests: list[FunctionalTest]) -> Verdict:
    total = len(tests)

    def fail(reason: str, passed: int = 0, detail: dict | None = None) -> Verdict:
        return Verdict(False, reason, total, passed, result.wall_seconds, detail, _tail(result.stderr))

    if result.timed_out:
        return fail(TIMEOUT)
    if result.output_limit_exceeded:
        return fail(OUTPUT_LIMIT)
    records: dict[int, dict] = {}
    done = None
    for line in result.stdout.decode("utf-8", "replace").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            return fail(MALFORMED_OUTPUT, detail={"line": line[:200]})
        if not isinstance(record, dict):
            return fail(MALFORMED_OUTPUT, detail={"line": line[:200]})
        if "load_error" in record:
            return fail(LOAD_ERROR, detail=record)
        if "done" in record:
            if done is not None:
                return fail(DUPLICATE_RESULT, detail={"done": record})
            done = record["done"]
            continue
        index = record.get("i")
        if not isinstance(index, int) or not 0 <= index < total:
            return fail(MALFORMED_OUTPUT, detail={"record": str(record)[:200]})
        if index in records:
            return fail(DUPLICATE_RESULT, detail={"i": index})
        records[index] = record
    if result.signal is not None or (result.exit_code not in (0, None)):
        # CPU limit (SIGKILL/SIGXCPU) and crashes land here.
        reason = TIMEOUT if result.signal in (9, 24) else RUNTIME_ERROR
        return fail(reason, sum(1 for i in records if _matches(tests[i], records[i])),
                    {"exit_code": result.exit_code, "signal": result.signal})
    if len(records) != total:
        missing = sorted(set(range(total)) - set(records))
        return fail(MISSING_RESULT, detail={"missing": missing[:20]})
    if done != total:
        return fail(INCOMPLETE, detail={"done": done})
    passed = 0
    first = None
    for i, test in enumerate(tests):
        record = records[i]
        if "error" in record:
            first = first or {"i": i, "reason": RUNTIME_ERROR, "error": record["error"], "detail": record.get("detail")}
            continue
        if _matches(test, record):
            passed += 1
        else:
            first = first or {"i": i, "reason": WRONG_ANSWER, "expected": test.expected,
                              "observed": _observed(test, record)}
    if passed == total:
        return Verdict(True, None, total, passed, result.wall_seconds, None, _tail(result.stderr))
    reason = first["reason"] if first else WRONG_ANSWER
    return fail(reason, passed, first)


def _observed(test: FunctionalTest, record: dict) -> Any:
    if test.compare == "return":
        return record.get("result")
    if test.compare.startswith("arg:"):
        k = int(test.compare.split(":", 1)[1])
        after = record.get("args_after") or []
        return after[k] if k < len(after) else None
    raise ValueError(f"unknown compare mode {test.compare!r}")


def _matches(test: FunctionalTest, record: dict) -> bool:
    if "error" in record:
        return False
    key_present = "result" in record if test.compare == "return" else "args_after" in record
    return key_present and values_equal(test.expected, _observed(test, record))


def tokens_equal(expected: str, observed: str) -> bool:
    exp, obs = expected.split(), observed.split()
    if len(exp) != len(obs):
        return False
    for e, o in zip(exp, obs):
        if e == o:
            continue
        try:
            if not math.isclose(float(e), float(o), rel_tol=FLOAT_REL_TOL, abs_tol=FLOAT_ABS_TOL):
                return False
            if "." not in e and "e" not in e.lower():
                return False  # integers must match exactly
        except ValueError:
            return False
    return True


def judge_stdin(
    candidate_source: str,
    tests: list[StdinTest],
    *,
    per_test_cpu_seconds: float = 2.0,
    wall_seconds: float = 30.0,
    memory_bytes: int = 512 * 1024 * 1024,
    checker_source: str | None = None,
    stop_on_first_failure: bool = True,
) -> Verdict:
    """Run each test in its own sandbox process; compare stdout on the host.

    With a checker (Open-R1 protocol), the checker runs in a separate sandbox as
    `checker.py input.txt expected.txt output.txt` and must print 1 (accept) or
    0 (reject) on its final stdout line; anything else is a checker error.
    """
    if not tests:
        return Verdict(False, NO_TESTS, 0, 0, 0.0)
    total, passed, spent = len(tests), 0, 0.0
    first = None
    stderr_tail = ""
    for i, test in enumerate(tests):
        remaining = wall_seconds - spent
        if remaining <= 0:
            return Verdict(False, TIMEOUT, total, passed, spent, {"i": i, "detail": "judge wall budget spent"}, stderr_tail)
        limits = sandbox.Limits(
            cpu_seconds=max(1, math.ceil(per_test_cpu_seconds)),
            wall_seconds=min(remaining, per_test_cpu_seconds * 3 + 1),
            memory_bytes=memory_bytes,
        )
        try:
            run = sandbox.run_python(
                "candidate.py",
                files={"candidate.py": candidate_source},
                stdin=test.input.encode("utf-8"),
                limits=limits,
            )
        except sandbox.SandboxUnavailable as exc:
            return Verdict(False, SANDBOX_ERROR, total, passed, spent, {"detail": str(exc)})
        spent += run.wall_seconds
        stderr_tail = _tail(run.stderr)
        reason = None
        if run.timed_out or run.signal in (9, 24):
            reason = TIMEOUT
        elif run.output_limit_exceeded:
            reason = OUTPUT_LIMIT
        elif run.exit_code != 0:
            reason = RUNTIME_ERROR
        else:
            observed = run.stdout.decode("utf-8", "replace")
            if checker_source is None:
                ok = tokens_equal(test.expected, observed)
            else:
                ok, checker_failure = _run_checker(checker_source, test, observed)
                if checker_failure:
                    return Verdict(False, CHECKER_ERROR, total, passed, spent, {"i": i, "detail": checker_failure}, stderr_tail)
            if not ok:
                reason = WRONG_ANSWER
        if reason is None:
            passed += 1
            continue
        first = first or {"i": i, "reason": reason, "exit_code": run.exit_code, "signal": run.signal}
        if stop_on_first_failure:
            break
    if passed == total:
        return Verdict(True, None, total, passed, spent, None, stderr_tail)
    return Verdict(False, first["reason"], total, passed, spent, first, stderr_tail)


def _run_checker(checker_source: str, test: StdinTest, observed: str) -> tuple[bool, str | None]:
    run = sandbox.run(
        [sandbox.PYTHON, "-I", "-S", "checker.py", "input.txt", "expected.txt", "output.txt"],
        files={
            "checker.py": checker_source,
            "input.txt": test.input,
            "expected.txt": test.expected,
            "output.txt": observed,
        },
        limits=sandbox.Limits(cpu_seconds=5, wall_seconds=10.0),
    )
    lines = run.stdout.decode("utf-8", "replace").strip().splitlines()
    if run.timed_out or run.exit_code != 0 or not lines:
        return False, f"checker produced no verdict (exit={run.exit_code}, timed_out={run.timed_out})"
    last = lines[-1].strip()
    if last == "1":
        return True, None
    if last == "0":
        return False, None
    return False, f"checker verdict unrecognized: {last[:80]!r}"
