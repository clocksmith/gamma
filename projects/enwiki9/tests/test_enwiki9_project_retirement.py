"""Archived projects cannot resume computation through the operational entrance."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import enwiki9_lab as lab


class ProjectRetirementTests(unittest.TestCase):
    def test_archive_blocks_execution_and_release_before_side_effects(self):
        for arguments in (["run"], ["release", "retained-job"],
                          ["enqueue", "retained-candidate"], ["discover-gates", "--dry-run"]):
            with self.subTest(arguments=arguments), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                state = root / "operations/runtime/project_status.json"
                state.parent.mkdir(parents=True)
                state.write_text(json.dumps({"status": "archived"}))
                stderr = io.StringIO()
                with patch.object(lab, "ROOT", root), patch.object(sys, "argv", ["lab", *arguments]), \
                        patch.object(lab, "ensure_layout") as initialize, redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as error:
                        lab.main()
                    self.assertEqual(error.exception.code, 2)
                    initialize.assert_not_called()
                self.assertIn("explicit user reopening", stderr.getvalue())
                self.assertFalse((root / "operations/adaptive").exists())

    def test_archive_keeps_status_inspection_available(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "operations/runtime/project_status.json"
            state.parent.mkdir(parents=True)
            state.write_text(json.dumps({"status": "archived"}))
            stdout = io.StringIO()
            with patch.object(lab, "ROOT", root), patch.object(sys, "argv", ["lab", "status"]), \
                    patch.object(lab, "ensure_layout"), \
                    patch.object(lab, "status_payload", return_value={"inspection": "available"}), \
                    redirect_stdout(stdout):
                self.assertEqual(lab.main(), 0)
            self.assertEqual(json.loads(stdout.getvalue()), {"inspection": "available"})

    def test_unreadable_authority_cannot_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "operations/runtime/project_status.json"
            state.parent.mkdir(parents=True)
            state.write_text("{broken")
            stderr = io.StringIO()
            with patch.object(lab, "ROOT", root), patch.object(sys, "argv", ["lab", "run"]), \
                    redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as error:
                    lab.main()
                self.assertEqual(error.exception.code, 2)
            self.assertIn("cannot establish project execution authority", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
