"""Automated checks for the standalone Mind Meld CLI."""

import subprocess
import sys
import unittest


try:  # pragma: no cover - runtime dependency detection
    import numpy  # noqa: F401
    _NUMPY_AVAILABLE = True
except ModuleNotFoundError:
    _NUMPY_AVAILABLE = False


class MindMeldCliTests(unittest.TestCase):
    """Basic smoke tests for the Mind Meld CLI entry point."""

    def test_help_invocation_succeeds(self) -> None:
        """The CLI should print help text and exit cleanly."""
        if not _NUMPY_AVAILABLE:
            self.skipTest("numpy is required to import the Mind Meld CLI")

        cmd = [sys.executable, "tools/run_mind_meld_cli.py", "--help"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        self.assertEqual(result.returncode, 0)
        # Help text should mention the CLI name for quick verification
        self.assertIn("Mind Meld CLI", result.stdout)


if __name__ == "__main__":
    unittest.main()
