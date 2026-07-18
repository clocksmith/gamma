from pathlib import Path
import unittest

from projects.enwiki9.tools.seal_cmix21_lstm200_fx2lite428_stats_recovery import (
    require_replay_invocation,
)


class ReplayInvocationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.backend = Path("/tmp/cmix.bin")
        self.dictionary = Path("/tmp/english.dic")
        self.store = Path("/tmp/input.store")
        self.archive = Path("/tmp/archive.bin")

    def require(self, guard: dict[str, list[str]]) -> None:
        require_replay_invocation(
            guard,
            backend=self.backend,
            dictionary=self.dictionary,
            store=self.store,
            archive=self.archive,
        )

    def test_accepts_wrapped_exact_command(self) -> None:
        self.require(
            {
                "command": [
                    "bash",
                    "-c",
                    'exec "$1" -r "$2" "$3" "$4" >"$5" 2>"$6"',
                    "_",
                    str(self.backend),
                    str(self.dictionary),
                    str(self.store),
                    str(self.archive),
                    "/tmp/stdout.log",
                    "/tmp/stderr.log",
                ]
            }
        )

    def test_accepts_direct_exact_command(self) -> None:
        self.require(
            {
                "command": [
                    str(self.backend),
                    "-r",
                    str(self.dictionary),
                    str(self.store),
                    str(self.archive),
                ]
            }
        )

    def test_rejects_shell_without_replay_mode(self) -> None:
        guard = {
            "command": [
                "bash",
                "-c",
                'exec "$1" "$2" "$3" "$4" >"$5" 2>"$6"',
                "_",
                str(self.backend),
                str(self.dictionary),
                str(self.store),
                str(self.archive),
            ]
        }
        with self.assertRaisesRegex(RuntimeError, "differs from frozen WRT replay"):
            self.require(guard)


if __name__ == "__main__":
    unittest.main()
