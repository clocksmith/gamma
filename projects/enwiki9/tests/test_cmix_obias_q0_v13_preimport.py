#!/usr/bin/env python3
"""Bounded v13 tests: inherited drift must fail before dynamic import."""

from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
COORDINATOR = PROJECT / "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v13.py"
GUARD = PROJECT / "tools/run_with_resource_guard_q0_v13.py"


class PreimportBootstrapTest(unittest.TestCase):
    def _assert_drift_precedes_import(
        self, entrypoint: Path, dependency_name: str, error_fragment: str
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            tools = project / "tools"
            tools.mkdir()
            copied = tools / entrypoint.name
            copied.write_bytes(entrypoint.read_bytes())
            marker = project / "inherited-import-executed"
            sentinel = tools / dependency_name
            sentinel.write_text(
                "from pathlib import Path\n"
                "Path(__file__).resolve().parents[1].joinpath("
                "'inherited-import-executed').write_text('bad')\n"
            )
            process = subprocess.run(
                [sys.executable, str(copied)],
                cwd=project,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(error_fragment, process.stderr)
            self.assertFalse(marker.exists(), "drifted inherited code executed")

    def test_coordinator_rejects_v12_drift_before_import(self) -> None:
        self._assert_drift_precedes_import(
            COORDINATOR,
            "cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v12.py",
            "pre-import dependency drift: coordinator_v12_base",
        )

    def test_guard_rejects_v12_drift_before_import(self) -> None:
        self._assert_drift_precedes_import(
            GUARD,
            "run_with_resource_guard_q0_v12.py",
            "pre-import guard dependency drift: resource_guard_v12_base",
        )

    def test_dynamic_import_syntax_is_after_verification_call(self) -> None:
        for entrypoint, report_name in (
            (COORDINATOR, "PREIMPORT_REPORT"),
            (GUARD, "PREIMPORT_GUARD_REPORT"),
        ):
            tree = ast.parse(entrypoint.read_text(), filename=str(entrypoint))
            report_line = next(
                node.lineno
                for node in tree.body
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == report_name
                    for target in node.targets
                )
            )
            importlib_line = next(
                node.lineno
                for node in tree.body
                if isinstance(node, ast.Import)
                and any(alias.name == "importlib.util" for alias in node.names)
            )
            self.assertLess(report_line, importlib_line)


if __name__ == "__main__":
    unittest.main()
