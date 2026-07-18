from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DELTA_PATH = (
    ROOT / "projects/enwiki9/programs/wikiir_prior_page_delta_v1/program.py"
)
PROBE_PATH = ROOT / "projects/enwiki9/tools/wikiir_prior_page_columnar_probe.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


DELTA = _load("wikiir_prior_page_delta_fixture", DELTA_PATH)
PROBE = _load("wikiir_prior_page_columnar_probe", PROBE_PATH)


def fixture_raw() -> bytes:
    pages = []
    for index in range(10):
        pages.append(
            b"<page><title>Page "
            + str(index).encode()
            + b"</title><text>{{box|name=Shared|value="
            + str(index).encode()
            + b"}}"
            + b" shared sentence" * 20
            + b"</text></page>\n"
        )
    return b"<mediawiki>\n" + b"".join(pages) + b"</mediawiki>"


def test_columnar_bundle_reconstructs_identical_interleaved_ir() -> None:
    ir, _stats = DELTA.encode_ir(fixture_raw())

    page_count, channels = PROBE.demultiplex(ir, DELTA)
    bundle, _channel_stats = PROBE.pack_bundle(page_count, channels)
    replay_count, replay_channels = PROBE.unpack_bundle(bundle)
    replay_ir = PROBE.multiplex(replay_count, replay_channels, DELTA)

    assert PROBE.multiplex(page_count, channels, DELTA) == ir
    assert replay_ir == ir
    assert DELTA.decode_ir(replay_ir) == fixture_raw()


def test_probe_receipt_closes_all_identity_gates(tmp_path: Path) -> None:
    input_path = tmp_path / "input"
    input_path.write_bytes(fixture_raw())

    receipt, bundle = PROBE.run(input_path, input_path.stat().st_size, DELTA_PATH)

    assert bundle.startswith(PROBE.BUNDLE_MAGIC)
    assert receipt["identity"]["multiplex_equals_original_ir"] is True
    assert receipt["identity"]["bundle_roundtrip_equals_original_ir"] is True
    assert receipt["identity"]["raw_roundtrip_ok"] is True
    assert receipt["promotion_authorized"] is False
