#!/usr/bin/env python3
"""CLI entrypoint for the BITS paired-switch experiment (`paired-switch-v1`).

Subcommands:
  verify-fixture   Build and verify canonical Section 1 `skip_equal` switch point.
  verify-engine    Run Sections 2-3 mechanical & numerical verification on BOTH
                   tied and untied PyTorch `transformers` causal LMs.
  verify-dev-suite Verify all 18 development problems (train + separate val),
                   helpers, and switch-time predictor decisions.
  qualify-helper   Stage 1: qualify `ordinary_named_fn` vs `no_helper` at equal
                   budgets under a whole-run exclusive GPU lease.
  run-stage2-val   Stage 2a: run paired vocabulary installation (`score_and_input_alias`
                   vs equally adapted `score_only_alias`, same helper & total budget)
                   on separate validation dev families under a whole-run GPU lease.
  eval-rung2       Stage 2b: score frozen transcript predictor against paired
                   validation installation outcomes vs 3 baselines.
  run-live         Stage 3a: run paired free-search comparison on a provisioned
                   local HuggingFace causal LM under a whole-run GPU lease.
  gate-rung3-dev   Stage 3b: evaluate development gate against frozen controls.
"""

from __future__ import annotations

import argparse
import errno
import fcntl
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import torch

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from dev_families import (
    ALL_DEV_PROBLEMS,
    DEV_PROBLEMS,
    DEV_VAL_PROBLEMS,
    get_dev_split,
    get_problem,
    verify_dev_family_suite,
)
from helpers import HELPER_SPECS, verify_all_helpers
from predictor import (
    evaluate_rung2_predictor,
    evaluate_rung3_dev_gate,
    evaluate_stage1_helper_qualification,
    is_full_run_gpu_reservation_verified,
    predict_switch_benefit,
    summarize_paired_search_outcomes,
)
from switch_engine import (
    ByteLevelTestTokenizer,
    HelperAliasTokenizer,
    PairedSwitchAdapter,
    PrefillState,
    adapt_arm_equal_budget,
    build_switch_adaptation_sequences,
    build_synthetic_transformer,
    get_peak_rss_bytes,
    run_forced_call_check,
    verify_cache_reuse_and_rebuild_parity,
)
from switch_point import (
    build_switch_point,
    restore_rng_state,
    save_switch_point,
    verify_switch_point_snapshot,
)
from verifier import (
    HELPER_TOKEN_SYMBOL,
    SingleBindRegistry,
    _ALIAS_IDENTIFIER,
    translate_alias_source,
    verify_candidate,
)
from work_budget import ArmBudget, OutOfBudget, positive_nanoseconds


FIXTURE_PATH = HERE / "fixtures" / "skip_equal_switch_point.json"
CONTRACT_PATH = HERE / "rung3_contract.json"


def cmd_verify_fixture(_args: argparse.Namespace) -> int:
    tok = ByteLevelTestTokenizer(helper_symbol=HELPER_TOKEN_SYMBOL, helper_token_id=259)
    problem = get_problem("rle_02_stream_diff_metrics")
    snapshot = build_switch_point(
        problem=problem,
        tokenizer_encode=tok.encode,
        helper_token_id=tok.helper_token_id,
        remaining_attempt_cap=32,
        remaining_token_budget=32 * 384,
        setup_budget_steps=16,
        seed=20261127,
    )
    save_switch_point(snapshot, FIXTURE_PATH)
    loaded = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    check = verify_switch_point_snapshot(loaded)
    print(json.dumps({"fixture_path": str(FIXTURE_PATH), "verification": check}, indent=2))
    return 0


def run_engine_verification(
    *,
    tie_word_embeddings: bool,
    device: str = "cpu",
    setup_budget_steps: int = 12,
) -> dict[str, Any]:
    """Run Sections 2-3 mechanical & numerical checks on a real transformers LlamaForCausalLM."""
    tok = ByteLevelTestTokenizer(helper_symbol=HELPER_TOKEN_SYMBOL, helper_token_id=259)
    problem = get_problem("rle_02_stream_diff_metrics")
    snapshot = build_switch_point(
        problem=problem,
        tokenizer_encode=tok.encode,
        helper_token_id=tok.helper_token_id,
        remaining_attempt_cap=32,
        remaining_token_budget=32 * 384,
        setup_budget_steps=setup_budget_steps,
        seed=20261127,
    )
    model = build_synthetic_transformer(
        vocab_size=tok.vocab_size,
        hidden_size=64,
        num_hidden_layers=2,
        num_attention_heads=4,
        tie_word_embeddings=tie_word_embeddings,
        seed=1337,
        device=device,
        dtype=torch.float32,
    )
    adapter = PairedSwitchAdapter(model, helper_token_id=tok.helper_token_id)
    try:
        adapt_examples = build_switch_adaptation_sequences(snapshot, tok.encode)

        arm_reports = {}
        arm_states = {}
        for arm in ("frozen_alias", "score_only_alias", "score_and_input_alias", "ordinary_named_fn"):
            res = adapt_arm_equal_budget(
                adapter,
                arm_name=arm,
                adaptation_examples=adapt_examples,
                setup_budget_steps=setup_budget_steps,
                lr=5e-2,
            )
            arm_states[arm] = res
            arm_reports[arm] = {k: v for k, v in res.items() if k not in ("delta_out", "delta_in")}

        # Confirm equal setup spend between score_only and score_and_input.
        so = arm_reports["score_only_alias"]
        si = arm_reports["score_and_input_alias"]
        equal_spend_ok = (
            so["actual_steps"] == si["actual_steps"] == setup_budget_steps
            and so["forward_passes"] == si["forward_passes"]
            and so["backward_passes"] == si["backward_passes"]
            and so["tokens_processed"] == si["tokens_processed"]
        )

        # Section 3A: forward-only KV-cache reuse + fresh boundary scoring + full rebuild parity.
        cont_text = (
            snapshot["switch_exposure"]["alias_arms"]
            + "\n[ASSISTANT]\ndef unique_zero_triplets(nums):\n    i = <H0>(xs, i)\n    return []\n"
        )
        cont_ids = tok.encode(cont_text)
        cache_check = verify_cache_reuse_and_rebuild_parity(
            adapter,
            prefix_token_ids=snapshot["prefix_token_ids"],
            continuation_token_ids=cont_ids,
            delta_out=arm_states["score_and_input_alias"]["delta_out"],
            delta_in=arm_states["score_and_input_alias"]["delta_in"],
            numerical_tol=1e-4,
        )

        # Section 3B: forced-call isolation check (exact shared output row, toggle only input row).
        pre_call_ids = tok.encode(
            snapshot["switch_exposure"]["alias_arms"].replace(HELPER_TOKEN_SYMBOL, "HELPER_OP")
            + "\n[ASSISTANT]\nj = "
        )
        forced_ops_ids = tok.encode("(xs, i)\n")
        forced_ver_ids = tok.encode(
            "\n[TOOL]\nVERIFIER_ATTEMPT_3: status=fail passed=2/3 first_failure_case=run_of_duplicates\n"
        )
        forced_check = run_forced_call_check(
            adapter,
            prefix_token_ids=snapshot["prefix_token_ids"],
            pre_call_tokens=pre_call_ids,
            forced_operands_and_body_tokens=forced_ops_ids,
            forced_verifier_response_tokens=forced_ver_ids,
            shared_delta_out=arm_states["score_and_input_alias"]["delta_out"],
            adapted_delta_in=arm_states["score_and_input_alias"]["delta_in"],
        )

        all_invariance_ok = all(
            r["invariance"]["backbone_and_other_rows_exact"]
            and r["invariance"]["arm_row_contract_ok"]
            for r in arm_reports.values()
        )
        passed = bool(
            equal_spend_ok
            and all_invariance_ok
            and cache_check["passed"]
            and forced_check["fixture_passed"]
            and forced_check["input_effect_isolated"]
        )
        return {
            "synthetic_mechanical_check_only": True,
            "trained_model_search_claim": False,
            "tie_word_embeddings": tie_word_embeddings,
            "adapter_detected_tied_embeddings": adapter.tied_embeddings,
            "device": device,
            "equal_spend_ok": equal_spend_ok,
            "all_invariance_ok": all_invariance_ok,
            "arms": arm_reports,
            "cache_reuse_check": cache_check,
            "forced_call_check": forced_check,
            "passed": passed,
        }
    finally:
        adapter.close()


def cmd_verify_engine(args: argparse.Namespace) -> int:
    results = {}
    for tied in (True, False):
        key = "tied_embeddings" if tied else "untied_embeddings"
        results[key] = run_engine_verification(
            tie_word_embeddings=tied,
            device=args.device,
            setup_budget_steps=args.setup_steps,
        )
    overall = all(r["passed"] for r in results.values())
    print(json.dumps({"overall_passed": overall, "modes": results}, indent=2))
    return 0 if overall else 1


def cmd_verify_dev_suite(_args: argparse.Namespace) -> int:
    helpers_receipt = verify_all_helpers()
    suite_receipt = verify_dev_family_suite(helper_token_id=259, problems=ALL_DEV_PROBLEMS)
    tok = ByteLevelTestTokenizer(helper_symbol=HELPER_TOKEN_SYMBOL, helper_token_id=259)

    split_reports = {}
    for split_name, probs in (("train", DEV_PROBLEMS), ("val", DEV_VAL_PROBLEMS)):
        pred_rows = []
        for prob in probs:
            for cap in (2, 32):
                snap = build_switch_point(
                    problem=prob,
                    tokenizer_encode=tok.encode,
                    helper_token_id=tok.helper_token_id,
                    remaining_attempt_cap=cap,
                    remaining_token_budget=cap * 384,
                    setup_budget_steps=16,
                    seed=20261127,
                )
                sanitized = dict(snap)
                sanitized["utility_regime"] = "REDACTED"
                pred = predict_switch_benefit(sanitized)
                pred_rows.append(
                    {
                        "problem_id": prob["problem_id"],
                        "family": prob["family"],
                        "utility_regime": prob["utility_regime"],
                        "attempt_cap": cap,
                        "decision": pred.decision,
                        "symptom_match_score": pred.symptom_match_score,
                        "predicted_net_benefit": pred.predicted_net_benefit,
                    }
                )
        useful_rows = [r for r in pred_rows if r["utility_regime"] != "irrelevant_decoy"]
        decoy_rows = [r for r in pred_rows if r["utility_regime"] == "irrelevant_decoy"]
        split_reports[split_name] = {
            "useful_adapt_rate": sum(1 for r in useful_rows if r["decision"] == "ADAPT") / len(useful_rows),
            "decoy_skip_rate": sum(1 for r in decoy_rows if r["decision"] == "SKIP") / len(decoy_rows),
            "rows": pred_rows,
        }

    out = {
        "helpers_verified": list(helpers_receipt.keys()),
        "suite": suite_receipt,
        "switch_predictor_offline_check": split_reports,
    }
    print(json.dumps(out, indent=2))
    return 0


def _default_gpu_lock_path(device: str) -> Path:
    env_path = os.environ.get("GAMMA_GPU_LOCK_PATH")
    if env_path:
        return Path(env_path)
    vis = (
        os.environ.get("CUDA_VISIBLE_DEVICES")
        or os.environ.get("HIP_VISIBLE_DEVICES")
        or os.environ.get("ROCR_VISIBLE_DEVICES")
        or "0"
    )
    tag = re.sub(r"[^a-zA-Z0-9_-]+", "_", f"{device}_{vis}").strip("_")
    return Path(f"/tmp/gamma-gpu-exclusive-{tag}.lock")


def check_exclusive_gpu(device: str, *, require_exclusive: bool = False) -> dict[str, Any]:
    """Point-in-time probe checking for competing GPU compute PIDs.

    NOTE: A single point-in-time probe is NOT sufficient for full-run GPU
    reservation. Live runs MUST wrap execution in `ExclusiveGpuLease`, which
    holds an OS-level `flock` across the entire run and polls this probe
    continuously via a background watchdog.
    """
    if device != "cuda":
        res = {
            "device": device,
            "exclusive_verified": False,
            "probe": "non_cuda_device",
            "foreign_pids": [],
            "reason": "Exclusive GPU verification requires --device cuda",
        }
        if require_exclusive:
            raise RuntimeError(res["reason"])
        return res

    my_pid = os.getpid()
    foreign_pids: list[int] = []
    probe = "none"
    if shutil.which("rocm-smi"):
        probe = "rocm-smi"
        proc = subprocess.run(
            ["rocm-smi", "--showpids"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        rc = getattr(proc, "returncode", 0)
        if isinstance(rc, int) and rc != 0:
            res = {
                "device": device,
                "exclusive_verified": False,
                "probe": "rocm-smi_error",
                "returncode": rc,
                "foreign_pids": [],
                "reason": f"rocm-smi --showpids exited with status {rc}",
            }
            if require_exclusive:
                raise RuntimeError(res["reason"])
            return res
        for line in proc.stdout.splitlines():
            m = re.match(r"^\s*(\d+)\s+\S+", line)
            if m:
                pid = int(m.group(1))
                if pid != my_pid:
                    foreign_pids.append(pid)
    elif shutil.which("nvidia-smi"):
        probe = "nvidia-smi"
        proc = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        rc = getattr(proc, "returncode", 0)
        if isinstance(rc, int) and rc != 0:
            res = {
                "device": device,
                "exclusive_verified": False,
                "probe": "nvidia-smi_error",
                "returncode": rc,
                "foreign_pids": [],
                "reason": f"nvidia-smi exited with status {rc}",
            }
            if require_exclusive:
                raise RuntimeError(res["reason"])
            return res
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line.isdigit():
                pid = int(line)
                if pid != my_pid:
                    foreign_pids.append(pid)
    else:
        res = {
            "device": device,
            "exclusive_verified": False,
            "probe": "unavailable",
            "foreign_pids": [],
            "reason": "Neither rocm-smi nor nvidia-smi found to verify exclusive GPU ownership",
        }
        if require_exclusive:
            raise RuntimeError(res["reason"])
        return res

    exclusive = len(foreign_pids) == 0
    res = {
        "device": device,
        "exclusive_verified": exclusive,
        "probe": probe,
        "self_pid": my_pid,
        "foreign_pids": sorted(set(foreign_pids)),
    }
    if require_exclusive and not exclusive:
        raise RuntimeError(
            f"Exclusive GPU check FAILED ({probe}): competing GPU PIDs active: {res['foreign_pids']}"
        )
    return res


class ExclusiveGpuLease:
    """Whole-run GPU reservation combining OS `flock` with a continuous PID watchdog.

    Guarantees:
    1. Acquires a non-blocking exclusive OS lock (`fcntl.flock(LOCK_EX | LOCK_NB)`)
       on a per-GPU lockfile before model load and holds it until final teardown,
       failing closed immediately if another run already holds the GPU.
    2. Performs an initial foreign-PID audit on acquire, runs a continuous daemon
       watchdog thread polling GPU compute PIDs throughout the entire run, and
       performs a final foreign-PID audit before releasing the lock.
    3. Records full-run telemetry (`lease_held_for_full_run`, `watchdog_polls`,
       `mid_run_intrusions`, `exclusive_maintained_throughout_run`, `lock_path`,
       `external_lease_id`) so receipts distinguish a full-run reservation from
       a point-in-time startup check.
    """

    def __init__(
        self,
        device: str,
        *,
        require_exclusive: bool = False,
        lock_path: str | Path | None = None,
        poll_interval_seconds: float = 5.0,
        external_lease_id: str | None = None,
        stage: str = "run",
    ) -> None:
        self.device = device
        self.require_exclusive = bool(require_exclusive)
        self.lock_path = Path(lock_path) if lock_path else (_default_gpu_lock_path(device) if device == "cuda" else None)
        self.poll_interval_seconds = max(0.01, float(poll_interval_seconds))
        self.external_lease_id = external_lease_id
        self.stage = stage

        self._fd: int | None = None
        self._stop_event = threading.Event()
        self._first_poll_done = threading.Event()
        self._state_lock = threading.Lock()
        self._watchdog_thread: threading.Thread | None = None
        self._watchdog_polls = 0
        self._mid_run_intrusions: list[dict[str, Any]] = []
        self._started_utc: str | None = None
        self._started_mono: float | None = None
        self._initial_check: dict[str, Any] | None = None
        self.report: dict[str, Any] = {}

    def _release_lock_fd(self) -> None:
        if self._fd is not None:
            fd = self._fd
            self._fd = None
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
            try:
                os.close(fd)
            except OSError:
                pass

    def _watchdog_loop(self) -> None:
        try:
            while not self._stop_event.is_set():
                try:
                    snap = check_exclusive_gpu(self.device, require_exclusive=False)
                except Exception as exc:  # pragma: no cover - defensive
                    snap = {
                        "exclusive_verified": False,
                        "probe": "watchdog_error",
                        "foreign_pids": [],
                        "reason": str(exc),
                    }
                with self._state_lock:
                    self._watchdog_polls += 1
                    if not snap.get("exclusive_verified", False):
                        self._mid_run_intrusions.append(
                            {
                                "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                "probe": snap.get("probe"),
                                "foreign_pids": list(snap.get("foreign_pids", [])),
                                "reason": snap.get("reason"),
                            }
                        )
                self._first_poll_done.set()
                if self._stop_event.wait(self.poll_interval_seconds):
                    break
        finally:
            self._first_poll_done.set()

    def __enter__(self) -> ExclusiveGpuLease:
        if self.device != "cuda":
            if self.require_exclusive:
                raise RuntimeError("Exclusive GPU reservation requires --device cuda")
            self.report = {
                "device": self.device,
                "reservation_mode": "none_non_cuda",
                "exclusive_verified": False,
                "lease_held_for_full_run": False,
                "exclusive_maintained_throughout_run": False,
                "probe": "non_cuda_device",
                "lock_path": None,
                "external_lease_id": self.external_lease_id,
                "watchdog_polls": 0,
                "mid_run_intrusions": [],
                "foreign_pids": [],
                "reason": "Exclusive GPU reservation requires --device cuda",
            }
            return self

        assert self.lock_path is not None
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(self.lock_path), os.O_CREAT | os.O_RDWR, 0o666)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            holder_info = ""
            if exc.errno in (errno.EACCES, errno.EAGAIN):
                try:
                    os.lseek(fd, 0, os.SEEK_SET)
                    holder_info = os.read(fd, 4096).decode("utf-8", errors="replace").strip()
                except OSError:
                    holder_info = ""
            os.close(fd)
            raise RuntimeError(
                f"GPU reservation lock {self.lock_path} is already held by another process"
                + (f": {holder_info}" if holder_info else "")
            ) from exc

        self._fd = fd
        self._started_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self._started_mono = time.perf_counter()
        meta = {
            "pid": os.getpid(),
            "host": socket.gethostname(),
            "device": self.device,
            "stage": self.stage,
            "started_at_utc": self._started_utc,
            "external_lease_id": self.external_lease_id,
        }
        payload_bytes = (json.dumps(meta, sort_keys=True) + "\n").encode("utf-8")
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, payload_bytes)
        os.fsync(fd)

        try:
            self._initial_check = check_exclusive_gpu(
                self.device, require_exclusive=self.require_exclusive
            )
        except Exception:
            self._release_lock_fd()
            raise

        self._stop_event.clear()
        self._first_poll_done.clear()
        self._watchdog_thread = threading.Thread(
            target=self._watchdog_loop,
            name=f"gamma-gpu-watchdog-{self.stage}",
            daemon=True,
        )
        self._watchdog_thread.start()
        self._first_poll_done.wait(timeout=max(2.0, self.poll_interval_seconds))
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self.device != "cuda":
            return
        self._stop_event.set()
        if self._watchdog_thread is not None:
            self._watchdog_thread.join(timeout=max(2.0, self.poll_interval_seconds + 1.0))
            self._watchdog_thread = None

        final_check = check_exclusive_gpu(self.device, require_exclusive=False)
        released_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        hold_seconds = round(
            time.perf_counter() - self._started_mono, 4
        ) if self._started_mono is not None else 0.0
        lease_held = self._fd is not None
        self._release_lock_fd()

        with self._state_lock:
            polls = self._watchdog_polls
            intrusions = list(self._mid_run_intrusions)

        init_ok = bool(self._initial_check and self._initial_check.get("exclusive_verified", False))
        final_ok = bool(final_check.get("exclusive_verified", False))
        maintained = bool(lease_held and init_ok and final_ok and polls >= 1 and len(intrusions) == 0)
        all_foreign = sorted(
            set((self._initial_check or {}).get("foreign_pids", []))
            | set(final_check.get("foreign_pids", []))
            | {pid for item in intrusions for pid in item.get("foreign_pids", [])}
        )
        self.report = {
            "device": self.device,
            "stage": self.stage,
            "reservation_mode": "flock_plus_continuous_watchdog",
            "lock_path": str(self.lock_path) if self.lock_path is not None else None,
            "external_lease_id": self.external_lease_id,
            "host": socket.gethostname(),
            "self_pid": os.getpid(),
            "started_at_utc": self._started_utc,
            "released_at_utc": released_utc,
            "hold_duration_seconds": hold_seconds,
            "poll_interval_seconds": self.poll_interval_seconds,
            "lease_held_for_full_run": lease_held,
            "watchdog_polls": polls,
            "mid_run_intrusions": intrusions,
            "initial_check": self._initial_check,
            "final_check": final_check,
            "probe": final_check.get("probe"),
            "foreign_pids": all_foreign,
            "exclusive_maintained_throughout_run": maintained,
            "exclusive_verified": maintained,
        }

    def raise_if_intruded(self) -> None:
        if self.require_exclusive and not self.report.get("exclusive_maintained_throughout_run", False):
            raise RuntimeError(
                "Exclusive GPU reservation was violated during the run: "
                f"intrusions={self.report.get('mid_run_intrusions')}, "
                f"final_check={self.report.get('final_check')}"
            )


_CODE_BLOCK_RE = re.compile(r"```(?:python|py|python3)?\s*\n(.*?)```", re.S)


def _extract_python_code(text: str, *, prompt_opened_fence: bool = False) -> str:
    if prompt_opened_fence:
        stripped = text.lstrip()
        if not stripped.startswith("```"):
            if "```" in text:
                first = text.split("```", 1)[0].strip()
                if first:
                    return first + "\n"
            return text.strip() + "\n"
    blocks = _CODE_BLOCK_RE.findall(text)
    if blocks:
        return blocks[-1].strip() + "\n"
    return text.strip() + "\n"


def _collect_eos_token_ids(tokenizer: Any, model: Any = None, *, exclude_id: int | None = None) -> set[int]:
    ids: set[int] = set()
    sources = [getattr(tokenizer, "eos_token_id", None)]
    gen_cfg = getattr(model, "generation_config", None) if model is not None else None
    if gen_cfg is not None:
        sources.append(getattr(gen_cfg, "eos_token_id", None))
    for src in sources:
        if isinstance(src, int):
            ids.add(src)
        elif isinstance(src, (list, tuple, set)):
            for item in src:
                if isinstance(item, int):
                    ids.add(item)
    if exclude_id is not None:
        ids.discard(int(exclude_id))
    return ids


def _sample_continuation_from_cache(
    adapter: PairedSwitchAdapter,
    *,
    past_key_values: Any,
    start_pos: int,
    prompt_suffix_ids: list[int],
    max_new_tokens: int,
    eos_token_id: int | set[int] | list[int] | tuple[int, ...] | None,
    temperature: float,
    budget: ArmBudget,
    stop_on_fence_close: bool = False,
    decode_fn: Callable[[list[int]], str] | None = None,
) -> tuple[list[int], int]:
    """Generate one candidate attempt forward-only from a cloned KV cache."""
    if prompt_suffix_ids:
        logits_seq, cache = adapter.forward_from_cache(
            past_key_values, start_pos=start_pos, new_token_ids=prompt_suffix_ids
        )
        next_logits = logits_seq[:, -1, :]
        pos = start_pos + len(prompt_suffix_ids)
    else:
        raise ValueError("prompt_suffix_ids must be non-empty")

    eos_ids: set[int] = set()
    if isinstance(eos_token_id, int):
        eos_ids.add(eos_token_id)
    elif isinstance(eos_token_id, (set, list, tuple)):
        eos_ids.update(int(x) for x in eos_token_id if isinstance(x, int))

    generated: list[int] = []
    with torch.no_grad():
        for _ in range(max_new_tokens):
            budget.checkpoint()
            if temperature <= 0.0:
                tok_id = int(next_logits.argmax(dim=-1).item())
            else:
                probs = torch.softmax(next_logits.to(torch.float32) / temperature, dim=-1)
                tok_id = int(torch.multinomial(probs, num_samples=1).item())
            generated.append(tok_id)
            if tok_id in eos_ids:
                break
            if stop_on_fence_close and decode_fn is not None and len(generated) >= 4:
                tail = decode_fn(generated[-4:])
                if "```" in tail:
                    break
            inp = torch.tensor([[tok_id]], dtype=torch.long, device=adapter.device)
            pos_ids = torch.tensor([[pos]], dtype=torch.long, device=adapter.device)
            budget.checkpoint()
            out = adapter.model(
                input_ids=inp,
                position_ids=pos_ids,
                past_key_values=cache,
                use_cache=True,
            )
            cache = out.past_key_values
            next_logits = out.logits[:, -1, :]
            pos += 1
    return generated, len(prompt_suffix_ids) + len(generated)


def _device_synchronizer(device: torch.device) -> Callable[[], None]:
    if device.type == "cuda":
        return lambda: torch.cuda.synchronize(device)
    if device.type == "mps":
        return torch.mps.synchronize
    return lambda: None


def verify_helper_token_roundtrip(alias_tokenizer: HelperAliasTokenizer) -> dict[str, Any]:
    """Verify `<H0>` encodes to one exact ID and decodes to an executable helper call."""
    sym = alias_tokenizer.helper_symbol
    hid = alias_tokenizer.helper_token_id
    encoded_sym = alias_tokenizer.encode(sym)
    if encoded_sym != [hid]:
        raise RuntimeError(
            f"Helper symbol {sym!r} must encode to single token ID [{hid}], got {encoded_sym!r}"
        )
    decoded_sym = alias_tokenizer.decode([hid], skip_special_tokens=True)
    if decoded_sym != sym:
        raise RuntimeError(
            f"Reserved token ID {hid} must decode to {sym!r}, got {decoded_sym!r}"
        )
    probe_src = f"def _bits_h0_probe(xs, i):\n    j = {sym}(xs, i)\n    return j\n"
    probe_ids = alias_tokenizer.encode(probe_src)
    hid_count = sum(1 for tid in probe_ids if tid == hid)
    if hid_count != 1:
        raise RuntimeError(
            f"Expected reserved token ID {hid} once in encoded probe source, found {hid_count}"
        )
    roundtrip_src = alias_tokenizer.decode(probe_ids, skip_special_tokens=True)
    binding = SingleBindRegistry().bind_once("skip_equal", hid, sym)
    lowered = translate_alias_source(roundtrip_src, binding, arm_uses_alias=True)
    calls = [0]
    impl = HELPER_SPECS["skip_equal"].implementation

    def _wrapped(*args: Any, **kwargs: Any) -> Any:
        calls[0] += 1
        return impl(*args, **kwargs)

    ns: dict[str, Any] = {_ALIAS_IDENTIFIER: _wrapped}
    exec(compile(lowered, "<h0-probe>", "exec"), ns)
    actual = ns["_bits_h0_probe"]([2, 2, 5], 0)
    if actual != 2 or calls[0] != 1:
        raise RuntimeError(
            f"Decoded helper token {sym!r} (id={hid}) did not execute bound helper cleanly: "
            f"actual={actual!r}, calls={calls[0]}"
        )
    return {
        "helper_symbol": sym,
        "helper_token_id": hid,
        "encoded_symbol_ids": encoded_sym,
        "decoded_symbol": decoded_sym,
        "probe_token_id_count": hid_count,
        "probe_executable_passed": True,
        "probe_runtime_helper_calls": calls[0],
    }


def _run_live_arm(
    arm: str,
    problem: dict[str, Any],
    snapshot: dict[str, Any],
    prefill: PrefillState | None,
    adapter: PairedSwitchAdapter,
    tokenizer: Any,
    budget: ArmBudget,
    *,
    attempt_cap: int,
    setup_steps: int,
    learning_rate: float,
    weight_decay: float = 0.0,
    max_new_tokens: int,
    verifier_timeout: float,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    no_helper = arm == "no_helper"
    alias = arm not in ("ordinary_named_fn", "no_helper")
    verify_ns = positive_nanoseconds(verifier_timeout)
    state = None
    solved = False
    status = "attempt_cap"
    blocked_phase = None
    attempts = checks = syntactic_calls = runtime_calls = generation_tokens = 0
    passing_syntactic_calls = passing_runtime_calls = 0
    verifier_statuses: dict[str, int] = {}
    partial_generation = False

    alias_tokenizer = (
        tokenizer
        if isinstance(tokenizer, HelperAliasTokenizer)
        else HelperAliasTokenizer(
            tokenizer,
            helper_token_id=adapter.helper_token_id,
            helper_symbol=HELPER_TOKEN_SYMBOL,
        )
    )

    try:
        budget.enter("setup")
        binding = (
            SingleBindRegistry().bind_once(problem["helper_name"], adapter.helper_token_id)
            if alias else None
        )

        def encode(text: str) -> list[int]:
            return alias_tokenizer.encode(text, add_special_tokens=False)

        examples = (
            build_switch_adaptation_sequences(snapshot, encode)
            if arm in ("score_only_alias", "score_and_input_alias") else []
        )
        budget.checkpoint()
        state = adapt_arm_equal_budget(
            adapter, arm_name=arm, adaptation_examples=examples, setup_budget_steps=setup_steps,
            lr=learning_rate, weight_decay=weight_decay, checkpoint=budget.checkpoint,
        )
        budget.checkpoint()
        adapter.set_deltas(state["delta_out"], state["delta_in"])
        restore_rng_state(snapshot["rng_state"])
        if no_helper:
            suffix = encode(
                "[SYSTEM_SWITCH]\nContinue solving using standard Python only (no external helper is provided).\n"
                "Return only the corrected Python function inside the code block.\n"
                "[ASSISTANT]\n```python\n"
            )
        else:
            exposure_key = "alias_arms" if alias else "ordinary_named_fn_arm"
            exposure = snapshot["switch_exposure"][exposure_key]
            suffix = encode(
                "[SYSTEM_SWITCH]\n"
                "The following tested helper operator is already bound in the runtime environment (do NOT redefine it). "
                "Use it if it directly fixes the failing failure mode; ignore it if the failure has an unrelated cause.\n"
                f"{exposure}\n"
                "Return only the corrected Python function inside the code block.\n"
                "[ASSISTANT]\n```python\n"
            )
        eos_ids = _collect_eos_token_ids(
            alias_tokenizer,
            getattr(adapter, "model", None),
            exclude_id=adapter.helper_token_id,
        )
        cases = problem["public_cases"] + problem["hidden_cases"]
        for attempt in range(attempt_cap):
            # An attempt cannot yield a verified solution without one full verifier window.
            budget.enter("generation", reserve_ns=verify_ns)
            attempts += 1
            partial_generation = True
            ids, tokens = _sample_continuation_from_cache(
                adapter, past_key_values=prefill.past_key_values,
                start_pos=len(snapshot["prefix_token_ids"]), prompt_suffix_ids=suffix,
                max_new_tokens=max_new_tokens, eos_token_id=eos_ids or alias_tokenizer.eos_token_id,
                temperature=0.0 if attempt == 0 else 0.7, budget=budget,
                stop_on_fence_close=True,
                decode_fn=lambda chunk: alias_tokenizer.decode(chunk, skip_special_tokens=True),
            )
            generation_tokens += tokens
            partial_generation = False
            source = _extract_python_code(
                alias_tokenizer.decode(ids, skip_special_tokens=True),
                prompt_opened_fence=True,
            )
            budget.enter("verification", reserve_ns=verify_ns)
            checks += 1
            verdict = verify_candidate(
                source,
                entry_point=problem["entry_point"],
                cases=cases,
                helper_name=None if no_helper else problem["helper_name"],
                binding=binding,
                arm_uses_alias=alias,
                timeout_seconds=verifier_timeout,
                deadline_ns=budget.deadline,
            )
            syn_c = int(verdict.get("syntactic_helper_calls", 0))
            run_c = int(verdict.get("runtime_helper_calls", 0))
            syntactic_calls += syn_c
            runtime_calls += run_c
            status = verdict["status"]
            verifier_statuses[status] = verifier_statuses.get(status, 0) + 1
            if verdict["passed"]:
                solved = True
                passing_syntactic_calls = syn_c
                passing_runtime_calls = run_c
                break
    except OutOfBudget as exc:
        blocked_phase = str(exc)

    spent_ns = budget.finish()
    if spent_ns > budget.limit_ns:
        blocked_phase = blocked_phase or budget.phase
    if blocked_phase is not None:
        solved = False
        passing_syntactic_calls = 0
        passing_runtime_calls = 0
        status = "budget_exhausted"

    seconds = spent_ns / 1e9
    record = {
        "problem_id": problem["problem_id"], "family": problem["family"],
        "helper_name": problem["helper_name"],
        "utility_regime": problem["utility_regime"],
        "switch_point_id": f"{problem['problem_id']}@cap{attempt_cap}", "attempt_cap": attempt_cap,
        "arm": arm, "solved": solved, "status": status, "attempts_started": attempts,
        "failed_attempts": attempts - int(solved),
        "verifier_calls": checks, "verifier_statuses": verifier_statuses,
        "helper_calls": syntactic_calls,
        "syntactic_helper_calls_all_attempts": syntactic_calls,
        "runtime_helper_calls_all_attempts": runtime_calls,
        "passing_syntactic_helper_calls": passing_syntactic_calls,
        "passing_runtime_helper_calls": passing_runtime_calls,
        "solved_with_executed_helper": bool(solved and passing_runtime_calls > 0),
        "setup_tokens": state["tokens_processed"] if state is not None else None,
        "setup_initial_loss": state.get("initial_loss") if state is not None else None,
        "setup_final_loss": state.get("final_loss") if state is not None else None,
        "setup_loss_position_counts": state.get("loss_position_counts") if state is not None else None,
        "generation_tokens_completed_attempts": generation_tokens, "interrupted_generation": partial_generation,
        "total_work_units": seconds, "elapsed_seconds": seconds,
        "work_to_first_verified": seconds if solved else None,
        "budget_limit_ns": budget.limit_ns, "phase_ns": budget.phase_ns,
        "remaining_ns": max(0, budget.limit_ns - spent_ns),
        "overrun_ns": max(0, spent_ns - budget.limit_ns), "blocked_phase": blocked_phase,
        "peak_memory_bytes": get_peak_rss_bytes(),
    }
    return record, state


def _make_gpu_lease(args: argparse.Namespace, *, stage: str) -> ExclusiveGpuLease:
    return ExclusiveGpuLease(
        args.device,
        require_exclusive=bool(getattr(args, "require_exclusive_gpu", False)),
        lock_path=getattr(args, "gpu_lock_path", None),
        poll_interval_seconds=float(getattr(args, "gpu_poll_interval", 5.0)),
        external_lease_id=getattr(args, "external_lease_id", None),
        stage=stage,
    )


def _add_gpu_lease_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--require-exclusive-gpu",
        action="store_true",
        help="Hold a whole-run exclusive GPU lock + continuous foreign-PID watchdog; fail closed on any intrusion",
    )
    parser.add_argument(
        "--gpu-lock-path",
        default=None,
        help="Override per-GPU flock path (default: $GAMMA_GPU_LOCK_PATH or /tmp/gamma-gpu-exclusive-<dev>.lock)",
    )
    parser.add_argument(
        "--gpu-poll-interval",
        type=float,
        default=5.0,
        help="Continuous GPU watchdog polling interval in seconds while the lease is held (default: 5.0)",
    )
    parser.add_argument(
        "--external-lease-id",
        default=None,
        help="Optional external host/cluster GPU reservation ID (e.g. Deco bus_lease) recorded in lockfile and receipt",
    )


def _verify_stage1_prereq(stage1_path: str | None, *, require_gpu_lease: bool) -> None:
    if not stage1_path:
        return
    s1 = json.loads(Path(stage1_path).read_text(encoding="utf-8"))
    if not s1.get("qualified"):
        raise SystemExit(f"Stage 1 gate NOT qualified ({stage1_path}): {s1.get('verdict')}")
    if require_gpu_lease and not is_full_run_gpu_reservation_verified(s1.get("exclusive_gpu_check")):
        raise SystemExit(
            f"Stage 1 receipt ({stage1_path}) lacks verified whole-run GPU reservation "
            "(point-in-time check is insufficient)."
        )


def _verify_stage2_prereq(stage2_path: str | None, *, require_gpu_lease: bool) -> None:
    if not stage2_path:
        return
    s2 = json.loads(Path(stage2_path).read_text(encoding="utf-8"))
    if not s2.get("rung2_earned"):
        raise SystemExit(f"Stage 2 Rung 2 gate NOT earned ({stage2_path}): {s2.get('verdict')}")
    if not (
        s2.get("same_helper_paired_installation_verified")
        and s2.get("matched_budget_and_adaptation_verified")
        and s2.get("validation_families_disjoint_from_train")
        and s2.get("install_arm") == "score_and_input_alias"
        and s2.get("baseline_arm") == "score_only_alias"
    ):
        raise SystemExit(
            f"Stage 2 receipt ({stage2_path}) is not backed by verified paired installation outcomes "
            "(score_and_input_alias vs score_only_alias on separate validation families)."
        )
    if require_gpu_lease and not (
        s2.get("outcomes_gpu_reserved_for_full_run")
        and is_full_run_gpu_reservation_verified(s2.get("outcomes_exclusive_gpu_check"))
    ):
        raise SystemExit(
            f"Stage 2 receipt ({stage2_path}) outcomes lack verified whole-run GPU reservation."
        )


def _run_paired_arms_loop(
    *,
    args: argparse.Namespace,
    contract: dict[str, Any],
    problems: list[dict[str, Any]],
    arm_names: list[str],
    stage_label: str,
    progress_prefix: str,
) -> dict[str, Any]:
    """Execute paired switch arms under one whole-run `ExclusiveGpuLease`."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    local_only = not args.allow_download
    dtype = torch.bfloat16 if args.dtype == "bfloat16" else torch.float32
    limit_ns = positive_nanoseconds(args.arm_budget_seconds)
    caps = [int(x.strip()) for x in args.attempt_caps.split(",") if x.strip()]
    setup_steps = int(args.setup_steps)
    max_new_tokens = int(contract["search_budgets"]["max_new_tokens_per_attempt"])
    timeout_s = float(contract["search_budgets"]["verifier_timeout_seconds"])

    records: list[dict[str, Any]] = []
    gate_receipts: list[dict[str, Any]] = []
    roundtrip_receipt: dict[str, Any] = {}
    preparation_seconds = 0.0

    gpu_lease = _make_gpu_lease(args, stage=stage_label)
    with gpu_lease:
        preparation_start = time.perf_counter()
        tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=local_only)
        if HELPER_TOKEN_SYMBOL not in tokenizer.get_vocab() and args.reserved_token_id is None:
            raise SystemExit(
                f"Model tokenizer does not reserve {HELPER_TOKEN_SYMBOL}; select a provisioned "
                f"unused special token ID via --reserved-token-id or reserve {HELPER_TOKEN_SYMBOL} "
                f"before creating the switch point."
            )

        helper_token_id = (
            int(args.reserved_token_id)
            if args.reserved_token_id is not None
            else int(tokenizer.convert_tokens_to_ids(HELPER_TOKEN_SYMBOL))
        )

        model = AutoModelForCausalLM.from_pretrained(
            args.model,
            torch_dtype=dtype,
            local_files_only=local_only,
        ).to(args.device).eval()

        adapter = PairedSwitchAdapter(model, helper_token_id=helper_token_id)
        alias_tokenizer = HelperAliasTokenizer(
            tokenizer,
            helper_token_id=helper_token_id,
            helper_symbol=HELPER_TOKEN_SYMBOL,
            vocab_size=min(adapter.vocab_size, int(adapter.lm_head.weight.shape[0])),
        )
        roundtrip_receipt = verify_helper_token_roundtrip(alias_tokenizer)
        sync = _device_synchronizer(adapter.device)
        sync()
        preparation_seconds = time.perf_counter() - preparation_start

        try:
            for prob in problems:
                for cap in caps:
                    snapshot_start = time.perf_counter()
                    snap = build_switch_point(
                        problem=prob,
                        tokenizer_encode=lambda s: alias_tokenizer.encode(s, add_special_tokens=False),
                        helper_token_id=helper_token_id,
                        remaining_attempt_cap=cap,
                        remaining_token_budget=cap * max_new_tokens,
                        setup_budget_steps=setup_steps,
                        seed=20261127,
                    )
                    # The snapshot supplies the completed search history and the fixed helper.
                    # Measure shared switch work once and debit its full cost to every continuation.
                    snapshot_seconds = time.perf_counter() - snapshot_start
                    shared = ArmBudget(limit_ns, synchronize=sync)
                    pred = predict_switch_benefit(snap)
                    prefill = None
                    try:
                        adapter.set_deltas(None, None)
                        shared.checkpoint()
                        prefill = adapter.prefill_prefix(snap["prefix_token_ids"])
                    except OutOfBudget:
                        pass
                    shared_ns = shared.finish()
                    joint_state = None
                    for arm in arm_names:
                        budget = ArmBudget(limit_ns, shared_setup_ns=shared_ns, synchronize=sync)
                        record, state = _run_live_arm(
                            arm, prob, snap, prefill, adapter, alias_tokenizer, budget,
                            attempt_cap=cap, setup_steps=setup_steps,
                            learning_rate=float(contract["adaptation_policy"]["learning_rate"]),
                            weight_decay=float(contract["adaptation_policy"].get("weight_decay", 0.0)),
                            max_new_tokens=max_new_tokens, verifier_timeout=timeout_s,
                        )
                        records.append(record)
                        if arm == "score_and_input_alias":
                            joint_state = state

                    # Offline diagnostic, performed only after paired search outcomes are fixed.
                    gate = {
                        "problem_id": prob["problem_id"], "attempt_cap": cap,
                        "switch_prediction": pred.decision,
                        "snapshot_preparation_seconds": snapshot_seconds,
                        "forced_call": {"status": "joint_setup_incomplete", "fixture_passed": False},
                    }
                    if joint_state is not None:
                        started = time.perf_counter()
                        h_spec = HELPER_SPECS[prob["helper_name"]]
                        h_lhs, h_rhs = h_spec.call_template.split("{OP}", 1)
                        fc = run_forced_call_check(
                            adapter, prefix_token_ids=snap["prefix_token_ids"],
                            pre_call_tokens=alias_tokenizer.encode(
                                snap["switch_exposure"]["alias_arms"].replace(HELPER_TOKEN_SYMBOL, "HELPER_OP")
                                + f"\n{h_lhs}", add_special_tokens=False,
                            ),
                            forced_operands_and_body_tokens=alias_tokenizer.encode(f"{h_rhs}\n", add_special_tokens=False),
                            forced_verifier_response_tokens=alias_tokenizer.encode(
                                "\n[TOOL]\nVERIFIER: retry\n", add_special_tokens=False,
                            ),
                            shared_delta_out=joint_state["delta_out"], adapted_delta_in=joint_state["delta_in"],
                        )
                        sync()
                        gate.update(forced_call=fc, diagnostic_seconds=time.perf_counter() - started)
                        if not fc["fixture_passed"]:
                            raise RuntimeError(f"Forced-call pre-call gate FAILED on {prob['problem_id']}: {fc}")
                    gate_receipts.append(gate)
                    recent = records[-len(arm_names):]
                    arm_bits = " ".join(
                        f"{r['arm']}={'PASS' if r['solved'] else r['status']}"
                        f"({r['attempts_started']}att,syn={r['syntactic_helper_calls_all_attempts']},"
                        f"pass_run={r['passing_runtime_helper_calls']},{r['elapsed_seconds']:.1f}s)"
                        for r in recent
                    )
                    print(
                        f"[{progress_prefix}] {prob['problem_id']} cap={cap}: {arm_bits}",
                        file=sys.stderr,
                        flush=True,
                    )
        finally:
            adapter.close()
            sync()

    return {
        "gpu_lease": gpu_lease,
        "limit_ns": limit_ns,
        "timeout_s": timeout_s,
        "caps": caps,
        "setup_steps": setup_steps,
        "preparation_seconds": preparation_seconds,
        "roundtrip_receipt": roundtrip_receipt,
        "gate_receipts": gate_receipts,
        "records": records,
    }


def cmd_run_live(args: argparse.Namespace) -> int:
    """Stage 3a: Run live free-search paired comparison on a user-provisioned HF causal LM."""
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if args.split == "sealed" and not args.sealed_problems_json:
        raise SystemExit("Refusing sealed run without explicit --sealed-problems-json")

    require_gpu = bool(getattr(args, "require_exclusive_gpu", False))
    stage1_path = getattr(args, "stage1_receipt", None)
    stage2_path = getattr(args, "stage2_receipt", None)
    _verify_stage1_prereq(stage1_path, require_gpu_lease=require_gpu)
    _verify_stage2_prereq(stage2_path, require_gpu_lease=require_gpu)

    dev_split = getattr(args, "dev_split", "train")
    if args.split == "dev":
        problems = DEV_PROBLEMS if dev_split == "train" else get_dev_split(dev_split)
    else:
        problems = json.loads(Path(args.sealed_problems_json).read_text(encoding="utf-8"))

    arm_names = [entry["name"] for entry in contract["arms"]]
    run_out = _run_paired_arms_loop(
        args=args,
        contract=contract,
        problems=problems,
        arm_names=arm_names,
        stage_label=f"stage3_run_live_{args.split}",
        progress_prefix="live-progress",
    )
    gpu_lease = run_out["gpu_lease"]
    summary = summarize_paired_search_outcomes(run_out["records"])
    payload = {
        "schema_version": "bits-paired-switch-live-receipt-v3",
        "work_unit": "synchronized_elapsed_seconds",
        "resident_model_preparation_seconds": run_out["preparation_seconds"],
        "budget_limit_ns_per_arm": run_out["limit_ns"],
        "verifier_reservation_ns": positive_nanoseconds(run_out["timeout_s"]),
        "exclusive_gpu_check": gpu_lease.report,
        "stage1_receipt_path": stage1_path,
        "stage2_receipt_path": stage2_path,
        "helper_token_roundtrip": run_out["roundtrip_receipt"],
        "model": args.model,
        "device": args.device,
        "dtype": args.dtype,
        "split": args.split,
        "dev_split": dev_split if args.split == "dev" else None,
        "attempt_caps": run_out["caps"],
        "setup_steps": run_out["setup_steps"],
        "gate_receipts": run_out["gate_receipts"],
        "summary": summary,
        "records": run_out["records"],
    }
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    gpu_lease.raise_if_intruded()
    print(json.dumps(summary, indent=2))
    return 0


def cmd_run_stage2_val(args: argparse.Namespace) -> int:
    """Stage 2a: Run paired installation vs equally adapted alias on separate validation dev families.

    Runs `score_only_alias` (equally adapted single-token alias) and
    `score_and_input_alias` (installed vocabulary entry) with the exact same
    helper, transcript, matched adaptation loss positions, and equal total
    wall-clock budget on `DEV_VAL_PROBLEMS` under a whole-run `ExclusiveGpuLease`.
    """
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    require_gpu = bool(getattr(args, "require_exclusive_gpu", False))
    stage1_path = getattr(args, "stage1_receipt", None)
    _verify_stage1_prereq(stage1_path, require_gpu_lease=require_gpu)

    arm_names = ["score_only_alias", "score_and_input_alias"]
    if getattr(args, "include_ordinary", False):
        arm_names.append("ordinary_named_fn")

    run_out = _run_paired_arms_loop(
        args=args,
        contract=contract,
        problems=list(DEV_VAL_PROBLEMS),
        arm_names=arm_names,
        stage_label="stage2_val_paired_installation",
        progress_prefix="stage2-val-progress",
    )
    gpu_lease = run_out["gpu_lease"]
    summary = summarize_paired_search_outcomes(run_out["records"])
    payload = {
        "schema_version": "bits-paired-switch-stage2-val-outcomes-v1",
        "work_unit": "synchronized_elapsed_seconds",
        "resident_model_preparation_seconds": run_out["preparation_seconds"],
        "budget_limit_ns_per_arm": run_out["limit_ns"],
        "verifier_reservation_ns": positive_nanoseconds(run_out["timeout_s"]),
        "exclusive_gpu_check": gpu_lease.report,
        "stage1_receipt_path": stage1_path,
        "helper_token_roundtrip": run_out["roundtrip_receipt"],
        "model": args.model,
        "device": args.device,
        "dtype": args.dtype,
        "split": "dev",
        "dev_split": "val",
        "paired_installation_arms": arm_names,
        "attempt_caps": run_out["caps"],
        "setup_steps": run_out["setup_steps"],
        "gate_receipts": run_out["gate_receipts"],
        "summary": summary,
        "records": run_out["records"],
    }
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    gpu_lease.raise_if_intruded()
    print(json.dumps(summary, indent=2))
    return 0


def cmd_qualify_helper(args: argparse.Namespace) -> int:
    """Stage 1: Qualify ordinary_named_fn vs no_helper at equal wall-clock budgets."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    local_only = not args.allow_download
    dtype = torch.bfloat16 if args.dtype == "bfloat16" else torch.float32
    limit_ns = positive_nanoseconds(args.arm_budget_seconds)
    problems = get_dev_split(args.dev_split)
    caps = [int(x.strip()) for x in args.attempt_caps.split(",") if x.strip()]
    max_new_tokens = int(contract["search_budgets"]["max_new_tokens_per_attempt"])
    timeout_s = float(contract["search_budgets"]["verifier_timeout_seconds"])
    records: list[dict[str, Any]] = []
    preparation_seconds = 0.0

    gpu_lease = _make_gpu_lease(args, stage="stage1_qualify_helper")
    with gpu_lease:
        preparation_start = time.perf_counter()
        tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=local_only)
        model = AutoModelForCausalLM.from_pretrained(
            args.model,
            torch_dtype=dtype,
            local_files_only=local_only,
        ).to(args.device).eval()

        # Reserve any non-EOS/BOS in-bounds ID strictly for switch-point schema construction.
        vocab_lim = int(model.get_input_embeddings().weight.shape[0])
        placeholder_hid = (
            int(args.reserved_token_id)
            if args.reserved_token_id is not None
            else vocab_lim - 1
        )
        adapter = PairedSwitchAdapter(model, helper_token_id=placeholder_hid)
        alias_tokenizer = HelperAliasTokenizer(
            tokenizer,
            helper_token_id=placeholder_hid,
            helper_symbol=HELPER_TOKEN_SYMBOL,
            vocab_size=min(adapter.vocab_size, int(adapter.lm_head.weight.shape[0])),
        )
        sync = _device_synchronizer(adapter.device)
        sync()
        preparation_seconds = time.perf_counter() - preparation_start

        try:
            for prob in problems:
                for cap in caps:
                    snap = build_switch_point(
                        problem=prob,
                        tokenizer_encode=lambda s: alias_tokenizer.encode(s, add_special_tokens=False),
                        helper_token_id=placeholder_hid,
                        remaining_attempt_cap=cap,
                        remaining_token_budget=cap * max_new_tokens,
                        setup_budget_steps=0,
                        seed=20261127,
                    )
                    shared = ArmBudget(limit_ns, synchronize=sync)
                    prefill = None
                    try:
                        adapter.set_deltas(None, None)
                        shared.checkpoint()
                        prefill = adapter.prefill_prefix(snap["prefix_token_ids"])
                    except OutOfBudget:
                        pass
                    shared_ns = shared.finish()

                    for arm in ("no_helper", "ordinary_named_fn"):
                        budget = ArmBudget(limit_ns, shared_setup_ns=shared_ns, synchronize=sync)
                        record, _ = _run_live_arm(
                            arm, prob, snap, prefill, adapter, alias_tokenizer, budget,
                            attempt_cap=cap, setup_steps=0, learning_rate=0.0,
                            max_new_tokens=max_new_tokens, verifier_timeout=timeout_s,
                        )
                        records.append(record)
                    recent = records[-2:]
                    arm_bits = " ".join(
                        f"{r['arm']}={'PASS' if r['solved'] else r['status']}"
                        f"({r['attempts_started']}att,syn={r['syntactic_helper_calls_all_attempts']},"
                        f"pass_run={r['passing_runtime_helper_calls']},{r['elapsed_seconds']:.1f}s)"
                        for r in recent
                    )
                    print(f"[stage1-progress] {prob['problem_id']} cap={cap}: {arm_bits}", file=sys.stderr, flush=True)
        finally:
            adapter.close()
            sync()

    min_fams = int(contract["stage1_helper_qualification"]["min_families_with_executed_helper_solve"])
    qualification = evaluate_stage1_helper_qualification(
        records, min_families_with_executed_helper_solve=min_fams
    )
    payload = {
        "schema_version": "bits-paired-switch-stage1-qualification-v2",
        "work_unit": "synchronized_elapsed_seconds",
        "resident_model_preparation_seconds": preparation_seconds,
        "budget_limit_ns_per_arm": limit_ns,
        "exclusive_gpu_check": gpu_lease.report,
        "model": args.model,
        "device": args.device,
        "dtype": args.dtype,
        "dev_split": args.dev_split,
        "attempt_caps": caps,
        **qualification,
        "records": records,
    }
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    gpu_lease.raise_if_intruded()
    print(json.dumps({k: v for k, v in qualification.items() if k != "arms"}, indent=2))
    return 0 if qualification["qualified"] else 2


def build_stage2_paired_installation_items(
    raw_outcomes: dict[str, Any],
    *,
    contract: dict[str, Any],
    dev_split: str = "val",
    install_arm: str = "score_and_input_alias",
    baseline_arm: str = "score_only_alias",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validate and construct Stage 2 paired installation evaluation items.

    Stage 2 MUST evaluate paired vocabulary-entry installation outcomes on the
    separate validation families (`DEV_VAL_PROBLEMS`, `dev_split == 'val'`),
    comparing the installed entry (`score_and_input_alias`) against the equally
    adapted single-token alias (`score_only_alias`) with the exact same helper,
    matched adaptation loss positions, and identical total budget.

    Stage 1 outcomes (`ordinary_named_fn` vs `no_helper`) measure helper
    usefulness, not vocabulary installation payoff, and are rejected fail-closed.
    """
    if dev_split != "val":
        raise SystemExit(
            f"Stage 2 must evaluate on separate validation dev families (--dev-split val), got {dev_split!r}"
        )
    if install_arm != "score_and_input_alias" or baseline_arm != "score_only_alias":
        raise SystemExit(
            "Stage 2 requires paired vocabulary-installation outcomes comparing "
            "install_arm='score_and_input_alias' vs baseline_arm='score_only_alias' "
            f"(got install_arm={install_arm!r}, baseline_arm={baseline_arm!r}). "
            "Stage 1 (ordinary_named_fn vs no_helper) tests helper usefulness, not installation payoff; "
            "collect paired validation outcomes with `run-stage2-val` first."
        )

    tok = ByteLevelTestTokenizer(helper_symbol=HELPER_TOKEN_SYMBOL, helper_token_id=259)
    val_problems = list(DEV_VAL_PROBLEMS)
    val_prob_by_id = {p["problem_id"]: p for p in val_problems}
    val_families = {p["family"] for p in val_problems}
    train_families = {p["family"] for p in DEV_PROBLEMS}

    records = raw_outcomes.get("records", [])
    by_key: dict[tuple[str, int], dict[str, dict[str, Any]]] = {}
    for rec in records:
        pid = rec.get("problem_id")
        if pid not in val_prob_by_id:
            continue
        by_key.setdefault((pid, int(rec["attempt_cap"])), {})[rec["arm"]] = rec

    eval_items: list[dict[str, Any]] = []
    pair_details: list[dict[str, Any]] = []
    seen_families: set[str] = set()
    for (pid, cap), arm_map in sorted(by_key.items()):
        if install_arm not in arm_map or baseline_arm not in arm_map:
            continue
        prob = val_prob_by_id[pid]
        if prob["family"] in train_families:
            raise SystemExit(f"Family {prob['family']!r} is not disjoint from train dev families")

        inst = arm_map[install_arm]
        base = arm_map[baseline_arm]

        # Enforce same helper on both arms.
        for label, rec in ((install_arm, inst), (baseline_arm, base)):
            rec_helper = rec.get("helper_name")
            if rec_helper is not None and rec_helper != prob["helper_name"]:
                raise SystemExit(
                    f"Helper mismatch on {pid}@cap{cap} ({label}): "
                    f"record={rec_helper!r}, expected={prob['helper_name']!r}"
                )

        # Enforce identical total wall-clock budget.
        inst_budget = inst.get("budget_limit_ns")
        base_budget = base.get("budget_limit_ns")
        if inst_budget is None or base_budget is None or int(inst_budget) <= 0 or int(inst_budget) != int(base_budget):
            raise SystemExit(
                f"Unequal or missing total budget on {pid}@cap{cap}: "
                f"{install_arm}={inst_budget!r}, {baseline_arm}={base_budget!r}"
            )

        # Enforce equally adapted arms (identical setup tokens & loss positions).
        inst_setup_tokens = inst.get("setup_tokens")
        base_setup_tokens = base.get("setup_tokens")
        inst_counts = inst.get("setup_loss_position_counts")
        base_counts = base.get("setup_loss_position_counts")
        if (
            inst_setup_tokens is None
            or base_setup_tokens is None
            or int(inst_setup_tokens) != int(base_setup_tokens)
            or not isinstance(inst_counts, dict)
            or not isinstance(base_counts, dict)
            or inst_counts != base_counts
            or int(inst_counts.get("selection", 0)) <= 0
            or int(inst_counts.get("post_call", 0)) <= 0
        ):
            raise SystemExit(
                f"Paired Stage 2 arms on {pid}@cap{cap} are not equally adapted: "
                f"{install_arm}=(tokens={inst_setup_tokens!r}, counts={inst_counts!r}), "
                f"{baseline_arm}=(tokens={base_setup_tokens!r}, counts={base_counts!r})"
            )

        inst_elapsed = float(inst.get("elapsed_seconds", inst.get("total_work_units", 0.0)))
        base_elapsed = float(base.get("elapsed_seconds", base.get("total_work_units", 0.0)))
        solve_delta = float(int(bool(inst["solved"])) - int(bool(base["solved"])))
        limit_s = float(int(inst_budget)) / 1e9
        time_penalty = (inst_elapsed - base_elapsed) / max(1.0, limit_s)
        realized_net = solve_delta - 0.1 * time_penalty

        snap = build_switch_point(
            problem=prob,
            tokenizer_encode=tok.encode,
            helper_token_id=tok.helper_token_id,
            remaining_attempt_cap=cap,
            remaining_token_budget=cap * int(contract["search_budgets"]["max_new_tokens_per_attempt"]),
            setup_budget_steps=int(contract["adaptation_policy"]["setup_budget_steps"]),
            seed=20261127,
        )
        seen_families.add(prob["family"])
        eval_items.append({"snapshot": snap, "realized_net_benefit": realized_net})
        pair_details.append(
            {
                "problem_id": pid,
                "family": prob["family"],
                "helper_name": prob["helper_name"],
                "attempt_cap": cap,
                "budget_limit_ns": int(inst_budget),
                "setup_tokens": int(inst_setup_tokens),
                "setup_loss_position_counts": inst_counts,
                "install_solved": bool(inst["solved"]),
                "baseline_solved": bool(base["solved"]),
                "install_elapsed_seconds": round(inst_elapsed, 4),
                "baseline_elapsed_seconds": round(base_elapsed, 4),
                "install_passing_runtime_helper_calls": int(inst.get("passing_runtime_helper_calls", 0)),
                "baseline_passing_runtime_helper_calls": int(base.get("passing_runtime_helper_calls", 0)),
                "realized_net_benefit": round(realized_net, 4),
            }
        )

    if not eval_items:
        raise SystemExit(
            f"No paired validation records found for ({install_arm!r}, {baseline_arm!r}) "
            "on DEV_VAL_PROBLEMS. Run `run-stage2-val` first."
        )
    missing_fams = sorted(val_families - seen_families)
    if missing_fams:
        raise SystemExit(
            f"Stage 2 validation outcomes are missing required separate validation families: {missing_fams}"
        )
    return eval_items, pair_details


def cmd_eval_rung2(args: argparse.Namespace) -> int:
    """Stage 2b: Score frozen helper-agnostic predictor on paired validation installation outcomes."""
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    s2_cfg = contract["stage2_rung2_prediction"]
    raw = json.loads(Path(args.outcomes_json).read_text(encoding="utf-8"))
    eval_items, pair_details = build_stage2_paired_installation_items(
        raw,
        contract=contract,
        dev_split=args.dev_split,
        install_arm=args.install_arm,
        baseline_arm=args.baseline_arm,
    )

    result = evaluate_rung2_predictor(
        eval_items,
        helper_length_threshold_lines=int(s2_cfg["helper_length_baseline_min_lines"]),
        min_win_recall=float(s2_cfg["require_predicts_both_losses_and_wins"]["min_win_recall"]),
        min_loss_recall=float(s2_cfg["require_predicts_both_losses_and_wins"]["min_loss_recall"]),
    )
    gpu_chk = raw.get("exclusive_gpu_check")
    result.update(
        {
            "schema_version": "bits-paired-switch-stage2-receipt-v2",
            "outcomes_json_path": str(args.outcomes_json),
            "dev_split": args.dev_split,
            "install_arm": args.install_arm,
            "baseline_arm": args.baseline_arm,
            "same_helper_paired_installation_verified": True,
            "matched_budget_and_adaptation_verified": True,
            "validation_families_disjoint_from_train": True,
            "paired_validation_units": len(eval_items),
            "outcomes_exclusive_gpu_check": gpu_chk,
            "outcomes_gpu_reserved_for_full_run": is_full_run_gpu_reservation_verified(gpu_chk),
            "paired_outcome_details": pair_details,
        }
    )
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["rung2_earned"] else 2


def cmd_gate_rung3_dev(args: argparse.Namespace) -> int:
    """Stage 3b: Evaluate Rung 3 development gate against frozen prerequisites and controls."""
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    s1 = json.loads(Path(args.stage1_receipt).read_text(encoding="utf-8")) if args.stage1_receipt else None
    s2 = json.loads(Path(args.stage2_receipt).read_text(encoding="utf-8")) if args.stage2_receipt else None
    s3 = json.loads(Path(args.stage3_receipt).read_text(encoding="utf-8"))
    verdict = evaluate_rung3_dev_gate(s3, contract=contract, stage1_receipt=s1, stage2_receipt=s2)
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(verdict, indent=2))
    return 0 if verdict["dev_gate_passed"] else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="BITS paired-switch experiment runner")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fix = sub.add_parser("verify-fixture", help="Build and verify canonical Section 1 skip_equal fixture")
    p_fix.set_defaults(func=cmd_verify_fixture)

    p_eng = sub.add_parser("verify-engine", help="Verify Sections 2-3 on tied and untied transformers LMs")
    p_eng.add_argument("--device", default="cpu", choices=["cpu", "mps", "cuda"])
    p_eng.add_argument("--setup-steps", type=int, default=12)
    p_eng.set_defaults(func=cmd_verify_engine)

    p_dev = sub.add_parser("verify-dev-suite", help="Verify Section 4 development families, helpers, and predictor")
    p_dev.set_defaults(func=cmd_verify_dev_suite)

    p_live = sub.add_parser("run-live", help="Stage 3a: run live free-search paired comparison on provisioned HF model")
    p_live.add_argument("--model", required=True, help="Local HF model directory or authorized repo id")
    p_live.add_argument("--device", default="cpu", choices=["cpu", "mps", "cuda"])
    p_live.add_argument("--dtype", default="float32", choices=["float32", "bfloat16"])
    p_live.add_argument("--split", default="dev", choices=["dev", "sealed"])
    p_live.add_argument("--dev-split", default="train", choices=["train", "val", "all"])
    p_live.add_argument("--sealed-problems-json", default=None)
    p_live.add_argument("--reserved-token-id", type=int, default=None)
    p_live.add_argument("--attempt-caps", default="2,32")
    p_live.add_argument("--setup-steps", type=int, default=16)
    p_live.add_argument("--arm-budget-seconds", required=True, type=float,
                        help="Identical total elapsed-time allowance per arm, from switch through verification")
    _add_gpu_lease_args(p_live)
    p_live.add_argument("--stage1-receipt", default=None, help="Optional Stage 1 qualification receipt to enforce")
    p_live.add_argument("--stage2-receipt", default=None, help="Optional Stage 2 Rung 2 receipt to enforce")
    p_live.add_argument("--allow-download", action="store_true", help="Explicitly authorize HF download")
    p_live.add_argument("--output", required=True)
    p_live.set_defaults(func=cmd_run_live)

    p_s1 = sub.add_parser("qualify-helper", help="Stage 1: qualify ordinary_named_fn vs no_helper at equal budgets")
    p_s1.add_argument("--model", required=True, help="Local HF model directory or authorized repo id")
    p_s1.add_argument("--device", default="cpu", choices=["cpu", "mps", "cuda"])
    p_s1.add_argument("--dtype", default="float32", choices=["float32", "bfloat16"])
    p_s1.add_argument("--dev-split", default="train", choices=["train", "val", "all"])
    p_s1.add_argument("--reserved-token-id", type=int, default=None)
    p_s1.add_argument("--attempt-caps", default="2,32")
    p_s1.add_argument("--arm-budget-seconds", required=True, type=float)
    _add_gpu_lease_args(p_s1)
    p_s1.add_argument("--allow-download", action="store_true")
    p_s1.add_argument("--output", required=True)
    p_s1.set_defaults(func=cmd_qualify_helper)

    p_s2_run = sub.add_parser(
        "run-stage2-val",
        help="Stage 2a: run paired installation (score_and_input_alias vs score_only_alias) on separate val dev families",
    )
    p_s2_run.add_argument("--model", required=True, help="Local HF model directory or authorized repo id")
    p_s2_run.add_argument("--device", default="cpu", choices=["cpu", "mps", "cuda"])
    p_s2_run.add_argument("--dtype", default="float32", choices=["float32", "bfloat16"])
    p_s2_run.add_argument("--reserved-token-id", type=int, default=None)
    p_s2_run.add_argument("--attempt-caps", default="2,32")
    p_s2_run.add_argument("--setup-steps", type=int, default=16)
    p_s2_run.add_argument("--arm-budget-seconds", required=True, type=float)
    p_s2_run.add_argument("--include-ordinary", action="store_true",
                          help="Also record ordinary_named_fn alongside the paired adapted arms")
    p_s2_run.add_argument("--stage1-receipt", default=None, help="Optional Stage 1 qualification receipt to enforce")
    _add_gpu_lease_args(p_s2_run)
    p_s2_run.add_argument("--allow-download", action="store_true")
    p_s2_run.add_argument("--output", required=True)
    p_s2_run.set_defaults(func=cmd_run_stage2_val)

    p_s2 = sub.add_parser(
        "eval-rung2",
        help="Stage 2b: score frozen predictor on paired installation outcomes on separate val dev families",
    )
    p_s2.add_argument("--outcomes-json", required=True,
                      help="Stage 2a `run-stage2-val` (or `run-live --dev-split val`) JSON receipt")
    p_s2.add_argument("--dev-split", default="val", choices=["val"])
    p_s2.add_argument("--install-arm", default="score_and_input_alias",
                      help="Installed vocabulary-entry arm (must be score_and_input_alias)")
    p_s2.add_argument("--baseline-arm", default="score_only_alias",
                      help="Equally adapted alias comparator (must be score_only_alias)")
    p_s2.add_argument("--output", default=None)
    p_s2.set_defaults(func=cmd_eval_rung2)

    p_s3 = sub.add_parser("gate-rung3-dev", help="Stage 3b: evaluate development gate against frozen controls")
    p_s3.add_argument("--stage1-receipt", default=None)
    p_s3.add_argument("--stage2-receipt", default=None)
    p_s3.add_argument("--stage3-receipt", required=True)
    p_s3.add_argument("--output", default=None)
    p_s3.set_defaults(func=cmd_gate_rung3_dev)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
