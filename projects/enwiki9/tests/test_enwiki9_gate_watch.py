from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


TOOL = Path(__file__).resolve().parents[1] / "tools/enwiki9_gate_watch.py"
SPEC = importlib.util.spec_from_file_location("enwiki9_gate_watch", TOOL)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def observation(**changes: object) -> dict[str, object]:
    base: dict[str, object] = {
        "progress_milestone": 25,
        "terminal": False,
        "rss_guard_exceeded": False,
        "official_decimal_over_limit_kib": 0,
        "memory_band": 0.90,
        "identity_ok": True,
        "heavy_lock_held": True,
        "pid_alive": True,
        "guard_status": "running",
    }
    base.update(changes)
    return base


def test_unchanged_observation_is_silent() -> None:
    current = observation()
    assert MODULE.event_reasons(current, dict(current), emit_initial=False) == []


def test_progress_only_emits_at_new_milestone() -> None:
    state = observation(progress_milestone=25)
    assert MODULE.event_reasons(
        observation(progress_milestone=30), state, emit_initial=False
    ) == ["progress_milestone"]


def test_guard_and_identity_changes_emit_immediately() -> None:
    reasons = MODULE.event_reasons(
        observation(rss_guard_exceeded=True, identity_ok=False),
        observation(),
        emit_initial=False,
    )
    assert "rss_guard_state" in reasons
    assert "candidate_identity" in reasons


def test_progress_parser_uses_latest_carriage_return_sample(tmp_path: Path) -> None:
    log = tmp_path / "stderr.log"
    log.write_text("progress: 4.99%\rprogress: 5.01%\r")
    assert MODULE.last_progress(log) == 5.01
    assert MODULE.milestone_for(5.01, 5) == 5
