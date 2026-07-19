from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "wikiir_url_prefix_reuse_probe.py"
SPEC = importlib.util.spec_from_file_location("wikiir_url_prefix_reuse_probe", TOOL)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_prefix_reference_beats_host_reference_when_learned() -> None:
    raw = b"http://example.test/first/a http://example.test/first/b"
    result = MODULE.run(raw)
    assert result["urls"] == 2
    assert result["prefix_references"] == 1
    assert result["incremental_path_prefix_bytes"] > 0
