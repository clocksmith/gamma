"""Component navigation preserves project-specific and versioned maps."""
import importlib.util
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("gamma_component_map", Path(__file__).resolve().parents[1] / "tools/catscan.py")
maps = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = maps
SPEC.loader.exec_module(maps)


class ComponentMapTests(unittest.TestCase):
    def test_published_index_excludes_another_sessions_untracked_study(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(maps, "ROOT", Path(directory).resolve()):
            root = Path(directory).resolve()
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            charter = root / "CATSCAN.md"
            charter.write_text("# CATSCAN: Family\n\nParent: none\n\n## Target\nOwn tracked source.\n")
            subprocess.run(["git", "-C", str(root), "add", "CATSCAN.md"], check=True)
            (root / "untracked-study").mkdir()
            (root / "untracked-study/CATSCAN.md").write_text("Unfinished private notes")
            self.assertEqual(maps.find_charter_paths(), [charter])

    def test_project_specific_format_and_long_invariants_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(maps, "ROOT", Path(directory).resolve()):
            root = Path(directory).resolve()
            source = root / "CATSCAN.md"
            source.write_text("# CATSCAN: Family\n\nParent: none\n\n## Target\nA useful component\nwith several versions.\n\n## Invariants\n" + "Preserve evidence. " * 200)
            charter, errors = maps.parse_charter(source)
            self.assertEqual(errors, [])
            self.assertEqual(charter.target, "A useful component with several versions.")
            self.assertEqual(maps.validate_charters([charter]), [])

    def test_same_family_name_keeps_distinct_version_paths(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(maps, "ROOT", Path(directory).resolve()):
            root = Path(directory).resolve()
            (root / "CATSCAN.md").write_text("# CATSCAN: Family\n\nParent: none\n\n## Target\nOwn versions.\n")
            for version in ("v1", "v2"):
                (root / version).mkdir()
                (root / version / "CATSCAN.md").write_text("# CATSCAN: Versioned study\n\nParent: [Family](../CATSCAN.md)\n\n## Target\nKeep the frozen mechanism.\n")
            charters = [maps.parse_charter(path)[0] for path in maps.find_charter_paths()]
            self.assertEqual(maps.validate_charters(charters), [])
            index = maps.render_index(charters)
            self.assertIn("v1/CATSCAN.md", index)
            self.assertIn("v2/CATSCAN.md", index)

    def test_missing_navigation_link_still_fails(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(maps, "ROOT", Path(directory).resolve()):
            path = Path(directory).resolve() / "CATSCAN.md"
            path.write_text("# CATSCAN: Family\n\nParent: none\n\n## Target\nOwn versions.\n\n## References\n[Absent](missing.py)\n")
            charter, errors = maps.parse_charter(path)
            self.assertEqual(errors, [])
            self.assertTrue(any("missing linked path" in error for error in maps.validate_charters([charter])))


if __name__ == "__main__":
    unittest.main()
