import unittest
from pathlib import Path

from projects.enwiki9.tools.seal_cmix21_lstm200_fx2lite428_allocator_recovery import (
    require_dictionary_codec_invocation,
    require_source_package,
)


class SourcePackageTest(unittest.TestCase):
    def test_accepts_complete_clean_package(self) -> None:
        require_source_package(
            {
                "schema": "reproducible_source_shar_package_v1",
                "proof": {
                    "proof_complete": True,
                    "clean_build_complete": True,
                    "clean_backend_identity": True,
                    "clean_program_identity": True,
                    "reference_backend_identity": True,
                },
            }
        )

    def test_rejects_package_without_clean_build(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "complete clean source proof"):
            require_source_package(
                {
                    "schema": "reproducible_source_shar_package_v1",
                    "proof": {"proof_complete": True},
                }
            )


class DictionaryCodecInvocationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.backend = Path("/tmp/cmix.bin")
        self.dictionary = Path("/tmp/english.dic")
        self.source = Path("/tmp/archive.bin")
        self.target = Path("/tmp/restored.raw")

    def require(self, command: list[str], mode: str = "-d") -> None:
        require_dictionary_codec_invocation(
            {"command": command},
            backend=self.backend,
            mode=mode,
            dictionary=self.dictionary,
            source=self.source,
            target=self.target,
        )

    def test_accepts_wrapped_decode(self) -> None:
        self.require(
            [
                "bash",
                "-c",
                'exec "$1" -d "$2" "$3" "$4" >"$5" 2>"$6"',
                "_",
                str(self.backend),
                str(self.dictionary),
                str(self.source),
                str(self.target),
                "/tmp/stdout.log",
                "/tmp/stderr.log",
            ]
        )

    def test_rejects_wrong_mode(self) -> None:
        command = [
            "bash",
            "-c",
            'exec "$1" -r "$2" "$3" "$4" >"$5" 2>"$6"',
            "_",
            str(self.backend),
            str(self.dictionary),
            str(self.source),
            str(self.target),
        ]
        with self.assertRaisesRegex(RuntimeError, "frozen dictionary codec"):
            self.require(command)


if __name__ == "__main__":
    unittest.main()
