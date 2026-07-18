from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "projects/enwiki9/programs/wikiir_prior_page_delta_v1/program.py"
SEALER_PATH = ROOT / "projects/enwiki9/tools/seal_wikiir_target_backend_probe.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


DELTA = _load("wikiir_delta_for_sealer", PROGRAM)
SEALER = _load("seal_wikiir_target_backend_probe", SEALER_PATH)


def test_terminal_archive_miss_seals_without_backend_decode(tmp_path: Path) -> None:
    raw = (
        b"<mediawiki><page><text>A</text></page>\n"
        b"<page><text>B</text></page></mediawiki>"
    )
    input_path = tmp_path / "input"
    input_path.write_bytes(raw)
    ir, _stats = DELTA.encode_ir(raw)
    ir_path = tmp_path / "input.ir"
    ir_path.write_bytes(ir)
    backend = tmp_path / "backend"
    backend.write_bytes(b"backend")
    dictionary = tmp_path / "dictionary"
    dictionary.write_bytes(b"dictionary")
    baseline = tmp_path / "baseline"
    baseline.write_bytes(b"HDRsmall")
    candidate = tmp_path / "candidate"
    candidate.write_bytes(b"a-much-larger-candidate")
    guard_path = tmp_path / "guard.json"
    guard_path.write_text(
        json.dumps(
            {
                "status": "complete",
                "returncode": 0,
                "limit_mode": "tree",
                "rss_guard_exceeded": False,
                "official_decimal_over_limit_kib": 0,
                "official_decimal_limit_kib": 1000,
                "max_sampled_tree_rss_kib": 900,
                "command": [
                    str(backend.resolve()),
                    "-c",
                    str(dictionary.resolve()),
                    str(ir_path.resolve()),
                    str(candidate.resolve()),
                ],
            }
        )
    )

    receipt = SEALER.run(
        input_path=input_path,
        scope_bytes=len(raw),
        ir_path=ir_path,
        wikiir_program=PROGRAM,
        backend=backend,
        dictionary=dictionary,
        baseline_archive=baseline,
        candidate_archive=candidate,
        guard_path=guard_path,
    )

    assert receipt["identity"]["raw_ir_roundtrip_ok"] is True
    assert receipt["identity"]["complete_native_archive_comparison"] is True
    assert receipt["identity"]["backend_decode_not_run_after_terminal_archive_miss"] is True
    assert receipt["metrics"]["wikiir_archive_delta_bytes"] > 0
    assert receipt["verdict"] == "retire_representation_on_target_backend_archive_miss"
    assert receipt["promotion_authorized"] is False
