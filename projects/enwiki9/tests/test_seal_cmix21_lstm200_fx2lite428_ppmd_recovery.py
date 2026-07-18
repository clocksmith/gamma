from pathlib import Path
import unittest

from projects.enwiki9.tools.seal_cmix21_lstm200_fx2lite428_ppmd_recovery import (
    require_guard_invocation,
)


class GuardInvocationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.wrapper = Path("/tmp/comp9")
        self.source = Path("/tmp/input.raw")
        self.target = Path("/tmp/archive.bin")

    def require(self, command: list[str], mode: str = "c") -> None:
        require_guard_invocation(
            {"command": command},
            wrapper=self.wrapper,
            mode=mode,
            source=self.source,
            target=self.target,
        )

    def test_accepts_direct_invocation(self) -> None:
        self.require(
            [str(self.wrapper), "c", str(self.source), str(self.target)]
        )

    def test_accepts_fixed_mode_shell_invocation(self) -> None:
        self.require(
            [
                "bash",
                "-c",
                'exec "$1" c "$2" "$3" >"$4" 2>"$5"',
                "_",
                str(self.wrapper),
                str(self.source),
                str(self.target),
                "/tmp/stdout.log",
                "/tmp/stderr.log",
            ]
        )

    def test_accepts_positional_mode_shell_invocation(self) -> None:
        self.require(
            [
                "/bin/bash",
                "-c",
                'exec "$1" "$2" "$3" "$4" >"$5" 2>"$6"',
                "_",
                str(self.wrapper),
                "c",
                str(self.source),
                str(self.target),
                "/tmp/stdout.log",
                "/tmp/stderr.log",
            ]
        )

    def test_rejects_wrong_fixed_mode(self) -> None:
        command = [
            "bash",
            "-c",
            'exec "$1" d "$2" "$3" >"$4" 2>"$5"',
            "_",
            str(self.wrapper),
            str(self.source),
            str(self.target),
        ]
        with self.assertRaisesRegex(RuntimeError, "differs from frozen invocation"):
            self.require(command, mode="c")


if __name__ == "__main__":
    unittest.main()
