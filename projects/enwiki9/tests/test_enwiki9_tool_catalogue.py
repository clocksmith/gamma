"""Static discovery, metadata drift and artifact publication regressions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.artifacts import artifact_ref, atomic_write, atomic_write_json
from tools import enwiki9_tool_catalogue as catalogue


class CatalogueTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "tools").mkdir()

    def write(self, relative, source):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
        return path

    def test_reads_metadata_without_importing_or_executing_tool(self):
        self.write("tools/runner.py", '\n'.join([
            '"""Reconstruct the fixture from a counted archive."""',
            'from pathlib import Path', 'import argparse',
            'from subprocess import run as launch',
            'MEMORY_BYTES = 4096',
            'TOOL_METADATA = {"outputs": ["results/fixture.json"]}',
            f'Path({str(self.root / "EXECUTED")!r}).write_text("bad")',
            'parser = argparse.ArgumentParser()',
            'parser.add_argument("--input", required=True, help="Exact fixture")',
            'launch(["false"])', 'raise RuntimeError("must never import this module")',
        ]))
        row, = catalogue.build_catalogue(self.root)
        self.assertFalse((self.root / "EXECUTED").exists())
        self.assertEqual(row["purpose"], "Reconstruct the fixture from a counted archive.")
        self.assertEqual(row["inputs"], ["CLI option --input"])
        self.assertEqual(row["outputs"], ["results/fixture.json"])
        self.assertEqual(row["resources"], ["MEMORY_BYTES=4096"])
        self.assertIn("subprocess.run", row["launch_capability"])
        self.assertTrue(row["launch_authority"].startswith("none"))
        self.assertEqual(row["arguments"][0]["help"], "Exact fixture")

    def test_contract_links_do_not_read_scientific_artifacts(self):
        self.write("tools/runner.py", '"""A frozen runner."""')
        self.write("operations/adaptive/experiments/example.json", json.dumps({
            "experimentId": "candidate", "inputs": [
                {"path": "tools/runner.py", "id": "runner"},
                {"path": "data/absent-science"}, {"path": ["malformed"]}],
            "outputs": ["results/candidate/decision.json"]}))
        row, = catalogue.build_catalogue(self.root)
        self.assertEqual(row["candidate_ids"], ["candidate"])
        self.assertEqual(row["contract_count"], 1)
        self.assertEqual(row["contract_outputs"], ["results/candidate/decision.json"])
        self.assertEqual(row["sources"], ["tools/runner.py", "operations/adaptive/experiments/example.json"])

    def test_missing_malformed_native_and_symlink_sources_remain_visible(self):
        self.write("tools/unknown.py", "x = 1\n")
        self.write("tools/broken.py", "def broken(:\n")
        self.write("tools/native/code.c", "// Exact byte fixture.\nint main(void) { return 0; }\n")
        outside = self.write("outside.py", 'raise AssertionError("not read")')
        (self.root / "tools/alias.py").symlink_to(outside)
        rows = {row["path"]: row for row in catalogue.build_catalogue(self.root)}
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows["tools/unknown.py"]["purpose"], catalogue.UNKNOWN)
        self.assertIn("unknown", rows["tools/unknown.py"]["launch_capability"])
        self.assertIn("SyntaxError", rows["tools/broken.py"]["diagnostics"][0])
        self.assertIn("symlink", rows["tools/alias.py"]["diagnostics"][0])
        self.assertNotIn("artifact", rows["tools/alias.py"])
        self.assertEqual(rows["tools/native/code.c"]["purpose"], "Exact byte fixture.")

    def test_preprocessor_directives_are_not_purpose_metadata(self):
        self.write("tools/source.cpp", "#include <cstdio>\nint main() {}\n")
        row, = catalogue.build_catalogue(self.root)
        self.assertEqual(row["purpose"], catalogue.UNKNOWN)

    def test_bad_contract_is_explicit_and_does_not_drop_tool(self):
        self.write("tools/tool.py", '"""Inspect records."""')
        self.write("operations/adaptive/experiments/bad.json", '{"inputs": null, "outputs": []}')
        row, = catalogue.build_catalogue(self.root)
        self.assertEqual(row["candidate_ids"], [])
        self.assertEqual(row["catalogue_diagnostics"][0]["reason"], "inputs and outputs must be arrays")

    def test_deterministic_generation_and_stale_coverage(self):
        self.write("tools/z.py", '"""Last tool."""')
        self.write("tools/a.py", '"""First tool."""')
        before = catalogue.build_catalogue(self.root)
        self.assertEqual(before, catalogue.build_catalogue(self.root))
        with patch.object(catalogue, "ROOT", self.root):
            self.assertEqual(catalogue.main([]), 0)
            self.assertEqual(catalogue.main(["--check"]), 0)
            self.write("tools/new.sh", "#!/bin/sh\n# Shell fixture.\nexit 0\n")
            self.assertEqual(catalogue.main(["--check"]), 1)
            self.assertEqual(catalogue.main([]), 0)
            (self.root / "tools/a.py").unlink()
            self.assertEqual(catalogue.main(["--check"]), 1)

    def test_durable_inventory_excludes_drafts_but_interactive_discovery_keeps_them(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)
        self.write("tools/tracked.py", '"""Tracked tool."""')
        self.write("tools/draft.py", '"""An independently owned draft."""')
        contract = {"experimentId": "selected", "inputs": [{"path": "tools/tracked.py"}], "outputs": []}
        self.write("operations/adaptive/experiments/tracked.json", json.dumps(contract))
        self.write("operations/adaptive/experiments/draft.json", json.dumps({**contract, "experimentId": "draft"}))
        subprocess.run(["git", "-C", str(self.root), "add", "tools/tracked.py", "operations/adaptive/experiments/tracked.json"],
                       check=True, capture_output=True)
        interactive = catalogue.build_catalogue(self.root)
        self.assertEqual({row["path"] for row in interactive}, {"tools/tracked.py", "tools/draft.py"})
        self.assertEqual(next(row for row in interactive if row["path"] == "tools/tracked.py")["candidate_ids"], ["draft", "selected"])
        durable, = catalogue.build_durable_catalogue(self.root)
        self.assertEqual(durable["path"], "tools/tracked.py")
        self.assertEqual(durable["candidate_ids"], ["selected"])
        with patch.object(catalogue, "ROOT", self.root):
            self.assertEqual(catalogue.main([]), 0)
            document = (self.root / "docs/tooling_inventory.md").read_text()
            self.assertNotIn("tools/draft.py", document)
            self.write("tools/draft.py", '"""Draft changed independently."""')
            self.assertEqual(catalogue.main(["--check"]), 0)
            subprocess.run(["git", "-C", str(self.root), "add", "tools/draft.py"], check=True, capture_output=True)
            self.assertEqual(catalogue.main(["--check"]), 1)


class ArtifactTests(unittest.TestCase):
    def test_fingerprint_rejects_escapes_and_aliases(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "root"
            root.mkdir()
            source = root / "source"
            source.write_bytes(b"fixture")
            reference = artifact_ref(source, root)
            self.assertEqual(reference, {"path": "source", "bytes": 7,
                                        "sha256": hashlib.sha256(b"fixture").hexdigest()})
            outside = base / "outside"
            outside.write_bytes(b"outside")
            with self.assertRaises(ValueError):
                artifact_ref(root / "../outside", root)
            (root / "alias").symlink_to(source)
            with self.assertRaisesRegex(ValueError, "symlink"):
                artifact_ref(root / "alias", root)

    def test_failed_atomic_publication_preserves_previous_document(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            atomic_write_json(path, {"state": "old"})
            with patch("lib.artifacts.os.replace", side_effect=OSError("publish failed")):
                with self.assertRaises(OSError):
                    atomic_write(path, b"new")
            self.assertEqual(json.loads(path.read_text()), {"state": "old"})
            self.assertEqual(list(path.parent.iterdir()), [path])


if __name__ == "__main__":
    unittest.main()
