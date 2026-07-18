from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "projects/enwiki9/tools"
sys.path.insert(0, str(TOOLS))

import enwiki9_status_receipt as status_receipt  # noqa: E402


def test_live_speedlab_gate_is_recovered_from_guard_command(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.raw"
    output_path = tmp_path / "archive.comp"
    guard_path = tmp_path / "guard.json"
    input_path.write_bytes(b"x" * 1234)
    output_path.write_bytes(b"archive")
    guard_path.write_text(
        json.dumps(
            {
                "status": "running",
                "sample_count": 17,
                "max_sampled_single_rss_kib": 7000,
                "max_sampled_tree_rss_kib": 7100,
                "latest_sample": {
                    "max_single_rss_kib": 6900,
                    "tree_rss_kib": 6950,
                },
            }
        )
    )
    args = " ".join(
        [
            "/usr/bin/python3",
            str(TOOLS / "run_with_rss_guard.py"),
            "--guard-json",
            str(guard_path),
            "--label",
            "matched_speedlab_1234",
            "--",
            "/tmp/cmix.bin",
            "-c",
            "/tmp/english.dic",
            str(input_path),
            str(output_path),
        ]
    )
    process_state = {"active_rows": [{"args": args}]}

    gate = status_receipt.live_speedlab_gate_from_process(process_state)

    assert gate is not None
    assert gate["candidate"] == "matched_speedlab_1234"
    assert gate["scope_bytes"] == 1234
    assert gate["verdict"] == "running"
    assert gate["rss_guard_status"] == "running"
    assert gate["sample_count"] == 17
    assert gate["single_rss_margin_kib"] == (
        status_receipt.LOCAL_RSS_GUARD_KIB - 7000
    )
    assert gate["driver_result_json_present"] is False
    assert gate["rss_guard_json_bytes"] == guard_path.stat().st_size
    assert gate["rss_guard_json_mtime_utc"] is not None
    assert len(gate["rss_guard_json_sha256"]) == 64


def test_live_speedlab_active_gate_preserves_source() -> None:
    gate = {
        "source": "live_speedlab_rss_guard",
        "candidate": "speedlab",
        "scope_bytes": 10_000_000,
        "verdict": "running",
    }

    row = status_receipt.active_gate_status_state(None, gate)

    assert row is not None
    assert row["source"] == "live_speedlab_rss_guard"
    assert row["program_id"] == "speedlab"
    assert row["scope_bytes"] == 10_000_000


def test_live_speedlab_skips_unexpanded_shell_guard_path(tmp_path: Path) -> None:
    input_path = tmp_path / "input.raw"
    output_path = tmp_path / "archive.comp"
    guard_path = tmp_path / "guard.json"
    input_path.write_bytes(b"x" * 64)
    guard_path.write_text(json.dumps({"status": "running", "sample_count": 3}))
    wrapper = {
        "args": (
            "/bin/bash -lc python3 run_with_rss_guard.py "
            "--guard-json $out/guard.json --label unresolved -- "
            "$out/cmix.bin -c $out/dic $out/in $out/archive"
        )
    }
    child = {
        "args": " ".join(
            [
                "/usr/bin/python3",
                str(TOOLS / "run_with_rss_guard.py"),
                "--guard-json",
                str(guard_path),
                "--label",
                "resolved",
                "--",
                "/tmp/cmix.bin",
                "-c",
                "/tmp/english.dic",
                str(input_path),
                str(output_path),
            ]
        )
    }

    gate = status_receipt.live_speedlab_gate_from_process(
        {"active_rows": [wrapper, child]}
    )

    assert gate is not None
    assert gate["candidate"] == "resolved"
    assert gate["rss_guard_json"] == str(guard_path)


def test_live_speedlab_uses_explicit_raw_scope_in_label(tmp_path: Path) -> None:
    transformed_input = tmp_path / "input.store"
    output_path = tmp_path / "archive.comp"
    guard_path = tmp_path / "guard.json"
    transformed_input.write_bytes(b"x" * 625)
    guard_path.write_text(json.dumps({"status": "running"}))
    args = " ".join(
        [
            "/usr/bin/python3",
            str(TOOLS / "run_with_rss_guard.py"),
            "--guard-json",
            str(guard_path),
            "--label",
            "compact_endpoint_10m_trace",
            "--",
            "/tmp/cmix.bin",
            "-r",
            "/tmp/english.dic",
            str(transformed_input),
            str(output_path),
        ]
    )

    gate = status_receipt.live_speedlab_gate_from_process(
        {"active_rows": [{"args": args}]}
    )

    assert gate is not None
    assert gate["scope_bytes"] == 10_000_000


def test_diagnostic_trace_contingency_forbids_scope_promotion() -> None:
    result = status_receipt.contingencies(
        "cmix21_lstm200_original_fx2_store_10m_trace", 10_000_000
    )

    assert result is not None
    assert result["if_passes"] == {
        "action": "run pinned matched replay and seal the trace receipt",
        "next_scope_bytes": None,
        "reason": (
            "a diagnostic trace is not a scored archive and cannot be "
            "promoted through the compression-gate scope ladder"
        ),
    }


def test_source_built_cmix_process_is_classified() -> None:
    row = {
        "args": "/tmp/source-build/cmix.bin -c /tmp/dic /tmp/in /tmp/out"
    }

    assert status_receipt.is_cmix_codec_row(row) is True


def test_wrapper_and_guard_processes_are_not_classified_as_cmix() -> None:
    wrapper = {"args": "/tmp/comp9a-decomp9 c /tmp/in /tmp/out"}
    guard = {
        "args": (
            "/usr/bin/python3 run_with_rss_guard.py -- "
            "/tmp/source-build/cmix.bin -c /tmp/dic /tmp/in /tmp/out"
        )
    }

    assert status_receipt.is_cmix_codec_row(wrapper) is False
    assert status_receipt.is_cmix_codec_row(guard) is False


def test_process_group_expansion_follows_new_session_child(monkeypatch) -> None:
    seed = {"pid": 10, "ppid": 9, "pgid": 100, "rss_kib": 1, "args": "guard"}
    rows = [
        {"pid": 9, "ppid": 1, "pgid": 100, "rss_kib": 1, "args": "runner"},
        seed,
        {
            "pid": 11,
            "ppid": 10,
            "pgid": 11,
            "rss_kib": 7000,
            "args": "/tmp/cmix.bin -c dic in out",
        },
    ]
    monkeypatch.setattr(status_receipt, "ps_all", lambda: rows)

    expanded = status_receipt.expand_process_groups([seed])

    assert {row["pid"] for row in expanded} == {9, 10, 11}
