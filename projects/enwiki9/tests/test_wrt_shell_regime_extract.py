import json
from pathlib import Path
import subprocess
import sys


TOOLS = Path(__file__).resolve().parents[1] / "tools"


def test_extract_preserves_overlapping_modes_as_mask(tmp_path: Path) -> None:
    cache = tmp_path / "cache.tsv"
    output = tmp_path / "regime.bin"
    receipt = tmp_path / "receipt.json"
    fields = [
        "pos",
        "bit_pos",
        "wrt_page_mode",
        "wrt_title_mode",
        "wrt_prose_mode",
        "wrt_ref_mode",
        "wrt_url_mode",
        "wrt_table_mode",
        "wrt_list_mode",
        "wrt_template_depth",
        "wrt_section_state",
    ]
    lines = ["\t".join(fields)]
    for pos in range(2):
        for bit_pos in range(8):
            values = [
                pos,
                bit_pos,
                1,
                int(pos == 0),
                1,
                int(pos == 1),
                0,
                0,
                int(pos == 1),
                0,
                0,
            ]
            lines.append("\t".join(map(str, values)))
    cache.write_text("\n".join(lines) + "\n")
    subprocess.run(
        [
            sys.executable,
            str(TOOLS / "wrt_shell_regime_extract.py"),
            str(cache),
            str(output),
            "--receipt",
            str(receipt),
        ],
        check=True,
    )
    assert output.read_bytes() == bytes([0x07] * 8 + [0x4D] * 8)
    data = json.loads(receipt.read_text())
    assert data["rows"] == 16
    assert data["regime_counts"] == {"0x07": 8, "0x4d": 8}
