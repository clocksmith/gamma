from __future__ import annotations

from pathlib import Path
import re


PATCH = (
    Path(__file__).resolve().parents[1]
    / "patches/compact_layer0_p1_trace_v1.patch"
)
HUNK = re.compile(r"^@@ -(\d+),(\d+) \+(\d+),(\d+) @@")


def test_every_unified_diff_hunk_has_exact_line_counts() -> None:
    lines = PATCH.read_text().splitlines()
    hunk_count = 0
    index = 0
    while index < len(lines):
        match = HUNK.match(lines[index])
        if match is None:
            index += 1
            continue
        hunk_count += 1
        expected_old = int(match.group(2))
        expected_new = int(match.group(4))
        old_count = 0
        new_count = 0
        index += 1
        while index < len(lines) and not lines[index].startswith(("@@ ", "diff --git ")):
            prefix = lines[index][:1]
            if prefix in {" ", "-"}:
                old_count += 1
            if prefix in {" ", "+"}:
                new_count += 1
            index += 1
        assert old_count == expected_old
        assert new_count == expected_new
    assert hunk_count == 4


def test_patch_instruments_prediction_loop_not_only_file_open() -> None:
    source = PATCH.read_text()

    assert 'OpenTrace("CMIX_LAYER0_P1_TRACE"' in source
    assert "WriteExact(layer0_p1_trace_" in source
    assert "Sigmoid::Logistic(p)" in source
