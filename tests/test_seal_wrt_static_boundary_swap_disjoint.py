from __future__ import annotations

import importlib.util
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "projects/enwiki9/tools/seal_wrt_static_boundary_swap_disjoint.py"
)
SPEC = importlib.util.spec_from_file_location("boundary_disjoint", TOOL)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_clean_guard_checks_decimal_and_binary_limits() -> None:
    clean = {
        "status": "complete",
        "returncode": 0,
        "rss_guard_exceeded": False,
        "official_decimal_over_limit_kib": 0,
    }
    assert MODULE.clean_guard(clean)
    assert not MODULE.clean_guard({**clean, "rss_guard_exceeded": True})
    assert not MODULE.clean_guard({**clean, "official_decimal_over_limit_kib": 1})


def test_artifact_hashes_payload(tmp_path: Path) -> None:
    payload = tmp_path / "payload"
    payload.write_bytes(b"abc")
    assert MODULE.artifact(payload)["sha256"] == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )
