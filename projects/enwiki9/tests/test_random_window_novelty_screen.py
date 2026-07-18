from __future__ import annotations

import importlib.util
import hashlib
import json
import sys
from types import SimpleNamespace
from pathlib import Path


TOOL = Path(__file__).resolve().parents[1] / "tools" / "random_window_novelty_screen.py"
SPEC = importlib.util.spec_from_file_location("random_window_novelty_screen", TOOL)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

FX2_GATE_TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "random_window_fx2_title_echo_gate.py"
)
sys.path.insert(0, str(FX2_GATE_TOOL.parent))
FX2_GATE_SPEC = importlib.util.spec_from_file_location(
    "random_window_fx2_title_echo_gate", FX2_GATE_TOOL
)
assert FX2_GATE_SPEC is not None and FX2_GATE_SPEC.loader is not None
FX2_GATE_MODULE = importlib.util.module_from_spec(FX2_GATE_SPEC)
sys.modules[FX2_GATE_SPEC.name] = FX2_GATE_MODULE
FX2_GATE_SPEC.loader.exec_module(FX2_GATE_MODULE)


SAMPLE = (
    b"<mediawiki>\n"
    b"<page><title>Alpha Engine</title><id>1000</id><revision><id>9000</id>"
    b'<contributor><id>75</id></contributor><text xml:space="preserve">'
    b"Alpha Engine uses [[Shared Target|one]] and [[Shared Target]]. "
    b"{{Infobox machine|name=Alpha Engine|name=Engine|url=https://example.org/a}} "
    b'<ref name="source">https://example.org/a</ref> ALPHA Alpha.'
    b"</text></revision></page>\n"
    b"<page><title>Beta Engine</title><id>1002</id><revision><id>9010</id>"
    b'<contributor><id>80</id></contributor><text xml:space="preserve">'
    b"Beta Engine uses [[Shared Target]] and [[Shared Target]]. "
    b"{{Infobox machine|name=Beta Engine|name=Engine|url=https://example.org/b}} "
    b'<ref name="source">https://example.org/b</ref> BETA Beta.'
    b"</text></revision></page>\n</mediawiki>"
) * 180


def test_all_transforms_roundtrip_and_are_deterministic() -> None:
    for transform in MODULE.transform_registry().values():
        encoded = transform.encode(SAMPLE)
        assert transform.decode(encoded) == SAMPLE, transform.name
        assert transform.encode(SAMPLE) == encoded, transform.name


def test_random_offsets_are_deterministic_stratified_and_phase_separated() -> None:
    first = MODULE.sample_offsets(1_000_000_000, 500_000, 6, 91, "selection")
    second = MODULE.sample_offsets(1_000_000_000, 500_000, 6, 91, "selection")
    confirmation = MODULE.sample_offsets(
        1_000_000_000, 500_000, 6, 91, "confirmation"
    )
    assert first == second
    assert first != confirmation
    assert len(set(first)) == 6
    for index, offset in enumerate(first):
        assert (999_500_000 * index) // 6 <= offset
        assert offset <= (999_500_000 * (index + 1)) // 6


def test_backend_evaluation_records_full_roundtrip() -> None:
    transform = MODULE.transform_registry()["wiki_graph_mtf256"]
    for backend in MODULE.backends():
        result = MODULE.evaluate(SAMPLE, transform, backend)
        assert result["transform_roundtrip_ok"] is True
        assert result["full_roundtrip_ok"] is True
        assert result["transform_deterministic"] is True
        assert result["archive_deterministic"] is True


def test_selection_requires_confirmation_before_fx2_trace() -> None:
    summary = {
        "algorithm": "candidate",
        "family": "candidate",
        "role": "candidate",
        "backend": "proxy",
        "window_size": 1_000_000,
        "gross_gain_bytes_per_million": 701.0,
        "all_roundtrip_ok": True,
        "all_deterministic": True,
    }
    selection = MODULE.family_decisions([summary], "selection")[0]
    confirmation = MODULE.family_decisions([summary], "confirmation")[0]
    assert selection["verdict"] == "confirmation_earned"
    assert confirmation["verdict"] == "exact_fx2_trace_earned"


def test_matched_control_cannot_promote() -> None:
    summary = {
        "algorithm": "control",
        "family": "control",
        "role": "matched_control",
        "backend": "proxy",
        "window_size": 1_000_000,
        "gross_gain_bytes_per_million": 10_000.0,
        "all_roundtrip_ok": True,
        "all_deterministic": True,
    }
    decision = MODULE.family_decisions([summary], "confirmation")[0]
    assert decision["verdict"] == "control_only"
    assert decision["proxy_fx2_trace_eligible"] is False


def test_recorded_receipts_bind_current_tool_and_disjoint_ranges() -> None:
    result_dir = Path(__file__).resolve().parents[1] / "results" / "random_window_novelty_v1"
    decision = json.loads((result_dir / "decision.json").read_text())
    selection_path = result_dir / "selection.json"
    confirmation_path = result_dir / "confirmation.json"
    selection = json.loads(selection_path.read_text())
    confirmation = json.loads(confirmation_path.read_text())

    assert hashlib.sha256(TOOL.read_bytes()).hexdigest() == decision["tool_sha256"]
    assert hashlib.sha256(selection_path.read_bytes()).hexdigest() == decision[
        "selection_receipt"
    ]["sha256"]
    assert hashlib.sha256(confirmation_path.read_bytes()).hexdigest() == decision[
        "confirmation_receipt"
    ]["sha256"]
    assert selection["tool_sha256"] == confirmation["tool_sha256"]
    assert selection["tool_sha256"] == decision["tool_sha256"]

    for selected in selection["windows"]:
        selected_range = range(
            selected["offset"], selected["offset"] + selected["window_size"]
        )
        for confirmed in confirmation["windows"]:
            confirmed_range = range(
                confirmed["offset"], confirmed["offset"] + confirmed["window_size"]
            )
            assert selected_range.stop <= confirmed_range.start or (
                confirmed_range.stop <= selected_range.start
            )


def test_fx2_gate_replays_frozen_window_with_matched_commands(tmp_path: Path) -> None:
    corpus = SAMPLE
    data_path = tmp_path / "enwik9"
    data_path.write_bytes(corpus)
    window_id = "confirmation-500000-0"
    confirmation = {
        "tool_sha256": hashlib.sha256(TOOL.read_bytes()).hexdigest(),
        "corpus_bytes": len(corpus),
        "corpus_sha256": hashlib.sha256(corpus).hexdigest(),
        "windows": [
            {
                "window_id": window_id,
                "window_size": len(corpus),
                "offset": 0,
                "sha256": hashlib.sha256(corpus).hexdigest(),
            }
        ],
    }
    confirmation_path = tmp_path / "confirmation.json"
    confirmation_path.write_text(json.dumps(confirmation))

    fake_cmix = tmp_path / "cmix"
    fake_cmix.write_text(
        "#!/usr/bin/env python3\n"
        "import shutil, sys\n"
        "shutil.copyfile(sys.argv[-2], sys.argv[-1])\n"
    )
    fake_cmix.chmod(fake_cmix.stat().st_mode | 0o111)
    dictionary = tmp_path / "english.dic"
    dictionary.write_bytes(b"dictionary")
    out_dir = tmp_path / "out"
    args = SimpleNamespace(
        data=data_path,
        confirmation=confirmation_path,
        window_id=window_id,
        cmix=fake_cmix,
        dictionary=dictionary,
        fx2_source_commit="test-source",
        fx2_source_tree_sha256="test-tree",
        fx2_source_diff_sha256="test-diff",
        build_contract="test-build",
        compiler="test-compiler",
        guard_script=FX2_GATE_MODULE.DEFAULT_GUARD,
        local_limit_kib=FX2_GATE_MODULE.LOCAL_10GIB_KIB,
        decimal_limit_kib=FX2_GATE_MODULE.DECIMAL_10GB_KIB,
        out_dir=out_dir,
    )

    receipt, exit_code = FX2_GATE_MODULE.run(args)

    assert exit_code == 0
    assert receipt["status"] == "complete"
    assert receipt["result"]["identity_roundtrip_ok"] is True
    assert receipt["result"]["candidate_roundtrip_ok"] is True
    assert receipt["result"]["identity_deterministic"] is True
    assert receipt["result"]["candidate_deterministic"] is True
    assert receipt["result"]["archive_delta_vs_identity"] < 0
    assert len(receipt["phases"]) == 6
    assert all(phase["returncode"] == 0 for phase in receipt["phases"])
    assert all(phase["guard"]["status"] == "complete" for phase in receipt["phases"])


def test_recorded_native_decision_binds_terminal_receipts() -> None:
    native_dir = (
        Path(__file__).resolve().parents[1]
        / "results"
        / "random_window_novelty_v1"
        / "fx2_native"
    )
    decision = json.loads((native_dir / "decision.json").read_text())
    assert decision["verdict"] == "retire_pre_wrt_title_echo_transform"
    assert decision["forecast_change_bytes"] == 0
    assert decision["aggregate_native"]["archive_delta_vs_identity"] > 0
    assert decision["aggregate_native"]["all_roundtrip_ok"] is True
    assert decision["aggregate_native"]["all_deterministic"] is True

    gate_tool_sha = hashlib.sha256(FX2_GATE_TOOL.read_bytes()).hexdigest()
    for row in decision["native_rows"]:
        receipt_path = Path(__file__).resolve().parents[1] / row["receipt_path"]
        assert hashlib.sha256(receipt_path.read_bytes()).hexdigest() == row[
            "receipt_sha256"
        ]
        receipt = json.loads(receipt_path.read_text())
        assert receipt["gate_tool"]["sha256"] == gate_tool_sha
        assert receipt["result"]["verdict"] == "negative_native_transfer"
        assert receipt["result"]["identity_roundtrip_ok"] is True
        assert receipt["result"]["candidate_roundtrip_ok"] is True
        assert receipt["result"]["identity_deterministic"] is True
        assert receipt["result"]["candidate_deterministic"] is True

    diagnostic_path = (
        Path(__file__).resolve().parents[1]
        / decision["wrt_diagnostic"]["receipt_path"]
    )
    assert hashlib.sha256(diagnostic_path.read_bytes()).hexdigest() == decision[
        "wrt_diagnostic"
    ]["receipt_sha256"]
