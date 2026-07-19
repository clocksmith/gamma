from pathlib import Path

from projects.enwiki9.tools.continue_endpoint428_pair_layer0_10m import (
    guard_command,
)


def test_guard_command_preserves_fixed_mode_identity() -> None:
    command = guard_command(
        run_guard=Path("/repo/run_with_rss_guard.py"),
        guard_json=Path("/proof/decode_guard.json"),
        label="decode",
        wrapper=Path("/proof/comp9a-decomp9"),
        mode="d",
        source=Path("/proof/archive.bin"),
        target=Path("/proof/restored.raw"),
        stdout_log=Path("/proof/stdout.log"),
        stderr_log=Path("/proof/stderr.log"),
    )

    assert "--official-decimal-limit-kib" in command
    assert 'exec "$1" d "$2" "$3" >"$4" 2>"$5"' in command
    assert command[-6:] == [
        "_",
        "/proof/comp9a-decomp9",
        "/proof/archive.bin",
        "/proof/restored.raw",
        "/proof/stdout.log",
        "/proof/stderr.log",
    ]
