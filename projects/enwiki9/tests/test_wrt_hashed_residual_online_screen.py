import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from seal_wrt_hashed_residual_online import FROZEN_VARIANT, window  # noqa: E402


def core_receipt(best_variant: str) -> dict:
    return {
        "schema_version": 2,
        "best_variant_id": best_variant,
        "baseline_payload_bytes": 100,
        "variants": [
            {
                "variant_id": FROZEN_VARIANT,
                "feature_mask": 0x201,
                "state_bytes": 12_582_912,
                "train_qbits": 10,
                "development_qbits": 8,
                "holdout_qbits": 6,
                "exact_saved_bytes": 2,
                "candidate_payload_bytes": 98,
                "positive_blocks": 1,
                "regressing_blocks": 0,
                "block_qbits": [24],
            }
        ],
    }


def write_fixture(tmp_path: Path, best_variant: str) -> tuple[Path, Path, Path, Path]:
    core = tmp_path / "core.json"
    core.write_text(json.dumps(core_receipt(best_variant)), encoding="utf-8")
    raw = tmp_path / "input.raw"
    trace = tmp_path / "probability.trace"
    store = tmp_path / "input.wrt.store"
    raw.write_bytes(b"raw")
    trace.write_bytes(b"trace")
    store.write_bytes(b"store")
    return core, raw, trace, store


def test_confirmation_uses_frozen_variant_not_local_selection(tmp_path: Path) -> None:
    core, raw, trace, store = write_fixture(tmp_path, "confirmation_local_winner")
    result = window(
        tmp_path,
        phase="confirmation",
        offset=10,
        scope_bytes=500_000,
        core_path=core,
        raw_path=raw,
        trace_path=trace,
        store_path=store,
    )
    assert result["locally_best_variant_id"] == "confirmation_local_winner"
    assert result["frozen_variant"]["variant_id"] == FROZEN_VARIANT
    assert result["frozen_variant"]["exact_saved_bytes_per_million"] == 4.0


def test_selection_rejects_a_different_winner(tmp_path: Path) -> None:
    core, raw, trace, store = write_fixture(tmp_path, "different_winner")
    with pytest.raises(ValueError, match="does not select"):
        window(
            tmp_path,
            phase="selection",
            offset=10,
            scope_bytes=500_000,
            core_path=core,
            raw_path=raw,
            trace_path=trace,
            store_path=store,
        )


@pytest.mark.skipif(shutil.which("g++") is None, reason="g++ unavailable")
def test_cpp_screen_builds_with_warnings_as_errors() -> None:
    source = TOOLS / "wrt_hashed_residual_online_screen.cpp"
    subprocess.run(
        ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-fsyntax-only", str(source)],
        check=True,
    )
