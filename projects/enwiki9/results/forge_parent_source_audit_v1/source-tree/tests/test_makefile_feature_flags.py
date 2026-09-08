"""Regression tests for fx3-cmix makefile feature-flag object selection."""

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def make_dry_run(extra_defines: str = "") -> str:
    """Return the make -n output for cmix with deterministic local flags."""
    defines = " ".join(
        flag
        for flag in [
            "-DSEED=923",
            "-DUPDATE_LIMIT=3000",
            extra_defines,
        ]
        if flag
    )
    result = subprocess.run(
        [
            "make",
            "-n",
            "CC=clang++",
            "COREI7=1",
            f"CFLAGS_DEFINES={defines}",
            "LFLAGS=-m64 -std=c++17",
            "cmix",
        ],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return result.stdout


class MakefileFeatureFlagTest(unittest.TestCase):
    """Protect default-off Hutter experiment hooks from changing default builds."""

    def test_default_build_uses_baseline_fxcm_without_payload_lex(self) -> None:
        output = make_dry_run()

        self.assertIn("src/models/fxcmv1.cpp", output)
        self.assertIn("fxcmv1.o", output)
        self.assertNotIn("src/models/fxcm_v26.cpp", output)
        self.assertNotIn("fxcm_v26.o", output)
        self.assertNotIn("r1_reorder_transform", output)

    def test_payload_lex_flag_adds_only_payload_transform(self) -> None:
        output = make_dry_run("-DFX3_ENABLE_PAYLOAD_LEX=1")

        self.assertIn("src/models/fxcmv1.cpp", output)
        self.assertIn("fxcmv1.o", output)
        self.assertNotIn("src/models/fxcm_v26.cpp", output)
        self.assertNotIn("fxcm_v26.o", output)
        self.assertIn("src/r1_reorder_transform.cpp", output)
        self.assertIn("r1_reorder_transform.o", output)

    def test_combined_flags_select_v26_and_payload_transform(self) -> None:
        output = make_dry_run(
            "-DFX3_ENABLE_FXCM_V26=1 -DFX3_ENABLE_PAYLOAD_LEX=1"
        )

        self.assertNotIn("src/models/fxcmv1.cpp", output)
        self.assertNotIn("fxcmv1.o", output)
        self.assertIn("src/models/fxcm_v26.cpp", output)
        self.assertIn("fxcm_v26.o", output)
        self.assertIn("src/r1_reorder_transform.cpp", output)
        self.assertIn("r1_reorder_transform.o", output)


if __name__ == "__main__":
    unittest.main()
