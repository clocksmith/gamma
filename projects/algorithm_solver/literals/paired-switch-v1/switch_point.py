"""Reproducible switch-point capture, serialization, and fail-closed verification.

Implements Section 1 of the BITS paired-switch experiment:
- Save a solver session after two attempts mishandle duplicate values (or the
  family's target failure mode).
- Capture exact token IDs, positions, verifier feedback, search frontier,
  remaining budget, and exact RNG states (Python, NumPy, PyTorch CPU).
- Reserve `<H0>` before the run and strictly verify its token ID and string
  appear NOWHERE in the saved prefix (system messages, attempts, tool/verifier
  responses, or pre-switch text).
- Expose the identical helper description, boundary behaviors, operand
  convention, assignment, arguments, punctuation, and syntax mask at the switch.
"""

from __future__ import annotations

import base64
import hashlib
import json
import random
from pathlib import Path
from typing import Any

import numpy as np
import torch

from helpers import HELPER_SPECS, verify_all_helpers
from verifier import HELPER_TOKEN_SYMBOL, SingleBindRegistry, verify_candidate


def capture_rng_state() -> dict[str, Any]:
    """Capture exact deterministic RNG state across Python, NumPy, and PyTorch CPU."""
    py_state = random.getstate()
    np_state = np.random.get_state()
    torch_bytes = torch.get_rng_state().cpu().numpy().tobytes()
    return {
        "python_version": py_state[0],
        "python_internal": list(py_state[1]),
        "python_gauss_next": py_state[2],
        "numpy_algo": str(np_state[0]),
        "numpy_keys": [int(x) for x in np_state[1].tolist()],
        "numpy_pos": int(np_state[2]),
        "numpy_has_gauss": int(np_state[3]),
        "numpy_cached_gaussian": float(np_state[4]),
        "torch_cpu_state_b64": base64.b64encode(torch_bytes).decode("ascii"),
    }


def restore_rng_state(state: dict[str, Any]) -> None:
    """Restore exact deterministic RNG state across Python, NumPy, and PyTorch CPU."""
    random.setstate((
        int(state["python_version"]),
        tuple(int(x) for x in state["python_internal"]),
        state["python_gauss_next"],
    ))
    np.random.set_state((
        str(state["numpy_algo"]),
        np.array(state["numpy_keys"], dtype=np.uint32),
        int(state["numpy_pos"]),
        int(state["numpy_has_gauss"]),
        float(state["numpy_cached_gaussian"]),
    ))
    raw = base64.b64decode(state["torch_cpu_state_b64"].encode("ascii"))
    tensor = torch.tensor(list(raw), dtype=torch.uint8)
    torch.set_rng_state(tensor)


def render_prefix_messages(
    problem_id: str,
    prompt_statement: str,
    attempts: list[dict[str, Any]],
) -> tuple[list[dict[str, str]], str]:
    """Render structured pre-switch transcript (strictly without any helper mention)."""
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are an algorithmic solver. Return a complete Python function matching the "
                "declared signature. Every candidate is checked by an isolated deterministic verifier."
            ),
        },
        {
            "role": "user",
            "content": f"PROBLEM_ID: {problem_id}\n{prompt_statement}",
        },
    ]
    for idx, att in enumerate(attempts, start=1):
        messages.append({"role": "assistant", "content": att["source"]})
        fb = att["verifier_feedback"]
        ff = fb.get("first_failure") or {}
        messages.append(
            {
                "role": "tool",
                "content": (
                    f"VERIFIER_ATTEMPT_{idx}: status={fb['status']} "
                    f"passed={fb['passed_cases']}/{fb['total_cases']} "
                    f"first_failure_case={ff.get('case')} "
                    f"error_type={ff.get('error_type')} "
                    f"message={ff.get('message')}"
                ),
            }
        )
    flat = "\n\n".join(f"[{m['role'].upper()}]\n{m['content']}" for m in messages) + "\n\n"
    return messages, flat


def assert_helper_token_absent(
    messages: list[dict[str, str]],
    prefix_text: str,
    prefix_token_ids: list[int],
    *,
    helper_token_symbol: str = HELPER_TOKEN_SYMBOL,
    helper_token_id: int,
) -> dict[str, Any]:
    """Fail-closed verification that `<H0>` appears nowhere in the saved prefix."""
    for idx, msg in enumerate(messages):
        if helper_token_symbol in msg["content"]:
            raise AssertionError(
                f"Reserved token symbol {helper_token_symbol} leaked into saved prefix message #{idx} ({msg['role']})"
            )
    if helper_token_symbol in prefix_text:
        raise AssertionError(f"Reserved token symbol {helper_token_symbol} found in flat prefix text")
    id_count = sum(1 for tid in prefix_token_ids if tid == helper_token_id)
    if id_count != 0:
        raise AssertionError(
            f"Reserved token id {helper_token_id} occurred {id_count} times in saved prefix_token_ids"
        )
    return {
        "helper_token_symbol": helper_token_symbol,
        "helper_token_id": helper_token_id,
        "prefix_token_count": len(prefix_token_ids),
        "prefix_symbol_occurrences": 0,
        "prefix_token_id_occurrences": 0,
        "absent_verified": True,
    }


def build_switch_point(
    *,
    problem: dict[str, Any],
    tokenizer_encode: Any,
    helper_token_id: int,
    remaining_attempt_cap: int,
    remaining_token_budget: int,
    setup_budget_steps: int,
    seed: int = 20261127,
    helper_token_symbol: str = HELPER_TOKEN_SYMBOL,
) -> dict[str, Any]:
    """Build and verify a complete reproducible switch point after two failed attempts."""
    helper_name = problem["helper_name"]
    spec = HELPER_SPECS[helper_name]
    helper_receipts = verify_all_helpers()

    # Run deterministic verifier on the two saved mishandling attempts (with no helper installed).
    verified_attempts = []
    for idx, src in enumerate(problem["failed_attempts"], start=1):
        verdict = verify_candidate(
            src,
            entry_point=problem["entry_point"],
            cases=problem["public_cases"],
            helper_name=None,
            binding=None,
            arm_uses_alias=False,
        )
        if verdict["passed"]:
            raise AssertionError(
                f"Pre-switch attempt #{idx} on {problem['problem_id']} unexpectedly passed public cases"
            )
        verified_attempts.append(
            {
                "attempt_index": idx,
                "source": src,
                "verifier_feedback": verdict,
            }
        )

    messages, prefix_text = render_prefix_messages(
        problem["problem_id"], problem["statement"], verified_attempts
    )
    prefix_token_ids = [int(t) for t in tokenizer_encode(prefix_text)]
    positions = list(range(len(prefix_token_ids)))

    absence_check = assert_helper_token_absent(
        messages,
        prefix_text,
        prefix_token_ids,
        helper_token_symbol=helper_token_symbol,
        helper_token_id=helper_token_id,
    )

    # Seed and capture exact switch-point RNG state.
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    rng_state = capture_rng_state()

    # Bind <H0> once for the session and verify immutability.
    registry = SingleBindRegistry()
    binding = registry.bind_once(helper_name, helper_token_id, helper_token_symbol)

    exposure_alias = spec.exposure_block(helper_token_symbol)
    exposure_ordinary = spec.exposure_block(helper_name)

    snapshot = {
        "schema_version": "bits-paired-switch-point-v1",
        "problem_id": problem["problem_id"],
        "family": problem["family"],
        "utility_regime": problem["utility_regime"],
        "entry_point": problem["entry_point"],
        "helper_name": helper_name,
        "helper_signature": spec.signature,
        "helper_implementation_sha256": spec.implementation_sha256(),
        "helper_boundary_receipt": helper_receipts[helper_name],
        "reserved_token": absence_check,
        "session_binding": {
            "helper_name": binding.helper_name,
            "token_symbol": binding.token_symbol,
            "token_id": binding.token_id,
            "implementation_sha256": binding.implementation_sha256,
            "bind_once_enforced": True,
        },
        "prefix_messages": messages,
        "prefix_text": prefix_text,
        "prefix_text_sha256": hashlib.sha256(prefix_text.encode("utf-8")).hexdigest(),
        "prefix_token_ids": prefix_token_ids,
        "positions": positions,
        "verifier_feedback": [a["verifier_feedback"] for a in verified_attempts],
        "search_frontier": {
            "attempts_completed_before_switch": len(verified_attempts),
            "failure_error_types": [
                (a["verifier_feedback"].get("first_failure") or {}).get("error_type")
                for a in verified_attempts
            ],
            "failure_cases": [
                (a["verifier_feedback"].get("first_failure") or {}).get("case")
                for a in verified_attempts
            ],
            "open_branches": 1,
        },
        "remaining_budget": {
            "remaining_attempts": remaining_attempt_cap,
            "remaining_generation_tokens": remaining_token_budget,
            "setup_budget_steps": setup_budget_steps,
            "remaining_verifier_calls": remaining_attempt_cap,
        },
        "switch_exposure": {
            "alias_arms": exposure_alias,
            "ordinary_named_fn_arm": exposure_ordinary,
            "matched_fields": [
                "description",
                "operand_convention",
                "assignment",
                "arguments",
                "punctuation",
                "syntax_mask",
                "boundary_behavior",
            ],
        },
        "rng_seed": seed,
        "rng_state": rng_state,
    }
    return snapshot


def verify_switch_point_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Re-verify every Section 1 invariant on a loaded switch-point JSON snapshot."""
    if snapshot.get("schema_version") != "bits-paired-switch-point-v1":
        raise AssertionError("Unexpected switch-point schema_version")
    helper_name = snapshot["helper_name"]
    spec = HELPER_SPECS[helper_name]
    if snapshot["helper_implementation_sha256"] != spec.implementation_sha256():
        raise AssertionError("Helper implementation hash drifted from tested implementation")
    if len(snapshot["prefix_token_ids"]) != len(snapshot["positions"]):
        raise AssertionError("prefix_token_ids and positions length mismatch")
    if snapshot["positions"] != list(range(len(snapshot["prefix_token_ids"]))):
        raise AssertionError("positions are not contiguous 0..L-1")
    if hashlib.sha256(snapshot["prefix_text"].encode("utf-8")).hexdigest() != snapshot["prefix_text_sha256"]:
        raise AssertionError("prefix_text_sha256 mismatch")

    absence = assert_helper_token_absent(
        snapshot["prefix_messages"],
        snapshot["prefix_text"],
        snapshot["prefix_token_ids"],
        helper_token_symbol=snapshot["reserved_token"]["helper_token_symbol"],
        helper_token_id=int(snapshot["reserved_token"]["helper_token_id"]),
    )

    # Confirm RNG state restores reproducibly to identical draws.
    restore_rng_state(snapshot["rng_state"])
    draw_a = (random.random(), float(np.random.rand()), float(torch.rand(1).item()))
    restore_rng_state(snapshot["rng_state"])
    draw_b = (random.random(), float(np.random.rand()), float(torch.rand(1).item()))
    if draw_a != draw_b:
        raise AssertionError(f"RNG restore non-deterministic: {draw_a} != {draw_b}")

    # Confirm matched switch exposure structure (identical after normalizing operator name).
    alias_exp = snapshot["switch_exposure"]["alias_arms"]
    ord_exp = snapshot["switch_exposure"]["ordinary_named_fn_arm"]
    sym = snapshot["reserved_token"]["helper_token_symbol"]
    if alias_exp.replace(sym, helper_name) != ord_exp:
        raise AssertionError("Alias and ordinary switch exposure blocks differ outside operator symbol")

    # Confirm bind-once enforcement rejects rebinding.
    reg = SingleBindRegistry()
    reg.bind_once(helper_name, int(snapshot["reserved_token"]["helper_token_id"]), sym)
    try:
        reg.bind_once(helper_name, int(snapshot["reserved_token"]["helper_token_id"]), sym)
    except RuntimeError:
        bind_once_ok = True
    else:
        raise AssertionError("SingleBindRegistry failed to reject second bind")

    return {
        "problem_id": snapshot["problem_id"],
        "helper_name": helper_name,
        "prefix_tokens": len(snapshot["prefix_token_ids"]),
        "absence_ok": absence["absent_verified"],
        "rng_restore_exact": True,
        "exposure_matched_exact": True,
        "bind_once_enforced": bind_once_ok,
        "helper_cases_passed": snapshot["helper_boundary_receipt"]["cases_passed"],
    }


def save_switch_point(snapshot: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
