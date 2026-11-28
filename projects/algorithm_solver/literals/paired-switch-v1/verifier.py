"""Deterministic isolated Python verifier for BITS paired-switch-v1.

Executes candidate programs in a subprocess with strict wall-clock timeouts,
translates reserved helper token `<H0>` to the single bound tested helper
implementation, validates matched syntax/operand masks, and keeps refusals
and timeouts explicitly in the denominator.
"""

from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any

from helpers import HELPER_SPECS, HelperSpec
from work_budget import OutOfBudget


HELPER_TOKEN_SYMBOL = "<H0>"
_ALIAS_IDENTIFIER = "__bits_h0_helper__"


@dataclass(frozen=True)
class SessionBinding:
    """Single immutable binding of `<H0>` for the remainder of a solver session."""

    helper_name: str
    token_symbol: str
    token_id: int
    implementation_sha256: str
    _bound: bool = True

    def assert_same_binding(self, helper_name: str, token_id: int) -> None:
        if helper_name != self.helper_name or token_id != self.token_id:
            raise RuntimeError(
                f"Attempted to rebind {self.token_symbol}: already bound once to "
                f"{self.helper_name} (token_id={self.token_id}), refused "
                f"{helper_name} (token_id={token_id})."
            )


class SingleBindRegistry:
    """Enforces that `<H0>` is bound at most once per session."""

    def __init__(self) -> None:
        self._binding: SessionBinding | None = None

    @property
    def binding(self) -> SessionBinding | None:
        return self._binding

    def bind_once(self, helper_name: str, token_id: int, token_symbol: str = HELPER_TOKEN_SYMBOL) -> SessionBinding:
        if self._binding is not None:
            raise RuntimeError(
                f"{token_symbol} is already bound once to {self._binding.helper_name} "
                f"(token_id={self._binding.token_id}); rebinding is forbidden."
            )
        if helper_name not in HELPER_SPECS:
            raise KeyError(f"Unknown helper: {helper_name}")
        spec = HELPER_SPECS[helper_name]
        self._binding = SessionBinding(
            helper_name=helper_name,
            token_symbol=token_symbol,
            token_id=token_id,
            implementation_sha256=spec.implementation_sha256(),
        )
        return self._binding


def count_helper_calls(source: str, operator_symbol: str) -> int:
    """Count syntactic calls to operator_symbol(...) in candidate source."""
    pattern = re.escape(operator_symbol) + r"\s*\("
    return len(re.findall(pattern, source))


def check_syntax_mask(source: str, spec: HelperSpec, operator_symbol: str) -> dict[str, Any]:
    """Check whether calls to operator_symbol conform to the matched operand/assignment mask."""
    total_calls = count_helper_calls(source, operator_symbol)
    mask_re = re.compile(spec.syntax_mask_regex.format(OP=re.escape(operator_symbol)))
    matched_calls = len(mask_re.findall(source))
    return {
        "operator_symbol": operator_symbol,
        "total_calls": total_calls,
        "mask_matched_calls": matched_calls,
        "mask_ok": total_calls == 0 or matched_calls == total_calls,
    }


def translate_alias_source(source: str, binding: SessionBinding | None, arm_uses_alias: bool) -> str:
    """Lower `<H0>` to an executable Python identifier pointing to the exact bound helper."""
    if not arm_uses_alias:
        if HELPER_TOKEN_SYMBOL in source:
            raise ValueError("Ordinary named-function arm may not emit reserved alias token <H0>")
        return source
    if binding is None:
        if HELPER_TOKEN_SYMBOL in source:
            raise ValueError("Candidate used <H0> before session binding was installed")
        return source
    return source.replace(binding.token_symbol, _ALIAS_IDENTIFIER)


_RUNNER_SNIPPET = r'''
import copy, json, sys, traceback

payload = json.loads(sys.stdin.read())
helper_source = payload.get("helper_source")
helper_name = payload.get("helper_name")
alias_ident = payload.get("alias_ident")
candidate_source = payload["candidate_source"]
entry_point = payload["entry_point"]
cases = payload["cases"]

ns = {}
if helper_source:
    exec(compile(helper_source, "<helper>", "exec"), ns)
    helper_fn = ns[helper_name]
    call_counter = [0]
    def _wrapped(*args, **kwargs):
        call_counter[0] += 1
        return helper_fn(*args, **kwargs)
    ns[helper_name] = _wrapped
    if alias_ident:
        ns[alias_ident] = _wrapped
else:
    call_counter = [0]

try:
    exec(compile(candidate_source, "<candidate>", "exec"), ns)
except Exception as exc:
    print(json.dumps({
        "status": "syntax_or_load_error",
        "passed": False,
        "passed_cases": 0,
        "total_cases": len(cases),
        "runtime_helper_calls": call_counter[0],
        "first_failure": {
            "case": "<compile>",
            "error_type": type(exc).__name__,
            "message": str(exc),
        },
    }))
    sys.exit(0)

fn = ns.get(entry_point)
if not callable(fn):
    print(json.dumps({
        "status": "missing_entrypoint",
        "passed": False,
        "passed_cases": 0,
        "total_cases": len(cases),
        "runtime_helper_calls": call_counter[0],
        "first_failure": {
            "case": "<entrypoint>",
            "error_type": "NameError",
            "message": f"Missing callable entrypoint `{entry_point}`",
        },
    }))
    sys.exit(0)

passed_cases = 0
first_failure = None
for idx, case in enumerate(cases):
    label = case.get("label", f"case_{idx}")
    args = copy.deepcopy(case["args"])
    expected = case["expected"]
    try:
        actual = fn(*args)
    except Exception as exc:
        if first_failure is None:
            first_failure = {
                "case": label,
                "error_type": type(exc).__name__,
                "message": str(exc),
                "args": case["args"],
                "expected": expected,
            }
        continue
    if actual == expected:
        passed_cases += 1
    elif first_failure is None:
        first_failure = {
            "case": label,
            "error_type": "WrongAnswer",
            "message": f"expected {expected!r}, got {actual!r}",
            "args": case["args"],
            "expected": expected,
            "actual": actual,
        }

ok = passed_cases == len(cases)
print(json.dumps({
    "status": "pass" if ok else "fail",
    "passed": ok,
    "passed_cases": passed_cases,
    "total_cases": len(cases),
    "runtime_helper_calls": call_counter[0],
    "first_failure": first_failure,
}))
'''


def verify_candidate(
    candidate_source: str,
    entry_point: str,
    cases: list[dict[str, Any]],
    *,
    helper_name: str | None = None,
    binding: SessionBinding | None = None,
    arm_uses_alias: bool = False,
    timeout_seconds: float = 2.0,
    deadline_ns: int | None = None,
) -> dict[str, Any]:
    """Execute candidate_source against deterministic cases in an isolated subprocess.

    Refusals, syntax errors, and timeouts are always returned as failed verdicts
    (never dropped from denominators).
    """
    started = time.perf_counter()
    if not candidate_source or not candidate_source.strip():
        return {
            "status": "refusal",
            "passed": False,
            "passed_cases": 0,
            "total_cases": len(cases),
            "syntactic_helper_calls": 0,
            "runtime_helper_calls": 0,
            "syntax_mask": None,
            "elapsed_seconds": time.perf_counter() - started,
            "first_failure": {
                "case": "<refusal>",
                "error_type": "EmptyOrRefusal",
                "message": "Empty candidate output",
            },
        }

    spec = HELPER_SPECS[helper_name] if helper_name else None
    operator_symbol = (
        binding.token_symbol
        if (arm_uses_alias and binding is not None)
        else (helper_name if helper_name else "")
    )
    syntax_mask = (
        check_syntax_mask(candidate_source, spec, operator_symbol)
        if (spec is not None and operator_symbol)
        else None
    )
    syntactic_calls = syntax_mask["total_calls"] if syntax_mask else 0

    try:
        lowered = translate_alias_source(candidate_source, binding, arm_uses_alias)
    except ValueError as exc:
        return {
            "status": "binding_violation",
            "passed": False,
            "passed_cases": 0,
            "total_cases": len(cases),
            "syntactic_helper_calls": syntactic_calls,
            "runtime_helper_calls": 0,
            "syntax_mask": syntax_mask,
            "elapsed_seconds": time.perf_counter() - started,
            "first_failure": {
                "case": "<binding>",
                "error_type": "BindingViolation",
                "message": str(exc),
            },
        }

    payload = {
        "helper_source": spec.source_code() if spec is not None else None,
        "helper_name": spec.name if spec is not None else None,
        "alias_ident": _ALIAS_IDENTIFIER if (arm_uses_alias and binding is not None) else None,
        "candidate_source": lowered,
        "entry_point": entry_point,
        "cases": copy.deepcopy(cases),
    }

    input_json = json.dumps(payload)
    if deadline_ns is not None:
        remaining = (deadline_ns - time.perf_counter_ns()) / 1e9
        if remaining <= 0:
            raise OutOfBudget("verification")
        timeout_seconds = min(timeout_seconds, remaining)

    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-c", _RUNNER_SNIPPET],
            input=input_json,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "passed": False,
            "passed_cases": 0,
            "total_cases": len(cases),
            "syntactic_helper_calls": syntactic_calls,
            "runtime_helper_calls": 0,
            "syntax_mask": syntax_mask,
            "elapsed_seconds": time.perf_counter() - started,
            "first_failure": {
                "case": "<timeout>",
                "error_type": "TimeoutExpired",
                "message": f"Execution exceeded {timeout_seconds:.2f}s",
            },
        }

    elapsed = time.perf_counter() - started
    if proc.returncode != 0 or not proc.stdout.strip():
        return {
            "status": "runtime_crash",
            "passed": False,
            "passed_cases": 0,
            "total_cases": len(cases),
            "syntactic_helper_calls": syntactic_calls,
            "runtime_helper_calls": 0,
            "syntax_mask": syntax_mask,
            "elapsed_seconds": elapsed,
            "first_failure": {
                "case": "<subprocess>",
                "error_type": "SubprocessCrash",
                "message": (proc.stderr or f"exit code {proc.returncode}").strip()[:400],
            },
        }

    result = json.loads(proc.stdout)
    result["syntactic_helper_calls"] = syntactic_calls
    result["syntax_mask"] = syntax_mask
    result["elapsed_seconds"] = elapsed
    result["helper_implementation_sha256"] = spec.implementation_sha256() if spec is not None else None
    return result
