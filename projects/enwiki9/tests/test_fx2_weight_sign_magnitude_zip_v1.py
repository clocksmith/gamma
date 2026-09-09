"""Exact archive membership and safe extraction using tiny synthetic sources."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import fx2_weight_sign_magnitude_zip_v1 as gate


class ZipTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'results')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self):
        source = self.root / 'source'
        source.mkdir()
        (source / 'makefile').write_bytes(b'all:\n\ttrue\n')
        (source / 'binary-data').write_bytes(bytes(range(256)))
        files = sorted(source.iterdir())
        options = 'make -j1\n'
        expected = {p.name: dict(bytes=p.stat().st_size, sha256=gate.digest(p.read_bytes())) for p in files}
        expected['invocation-and-build.txt'] = dict(bytes=len(options), sha256=gate.digest(options.encode()))
        a, b = self.root / 'a.zip', self.root / 'b.zip'
        gate.write_bundle(a, source, files, options)
        gate.write_bundle(b, source, files, options)
        return a, b, expected

    def test_exact_repeat_and_extraction(self):
        a, b, expected = self.fixture()
        self.assertEqual(a.read_bytes(), b.read_bytes())
        target = self.root / 'relocated'
        gate.extract_exact(a, target, expected)
        for name, row in expected.items():
            self.assertEqual(gate.digest((target / name).read_bytes()), row['sha256'])
        with self.assertRaises(FileExistsError):
            gate.extract_exact(a, target, expected)

    def test_missing_member_rejected_before_extraction(self):
        a, _, expected = self.fixture()
        expected.pop('makefile')
        target = self.root / 'bad'
        with self.assertRaisesRegex(ValueError, 'member set'):
            gate.extract_exact(a, target, expected)
        self.assertFalse(target.exists())

    def test_corrupted_content_rejected(self):
        a, _, expected = self.fixture()
        expected['makefile']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'hash differs'):
            gate.extract_exact(a, self.root / 'bad', expected)

    def test_parent_traversal_rejected(self):
        archive = self.root / 'bad.zip'
        with zipfile.ZipFile(archive, 'x') as z:
            info = zipfile.ZipInfo('../escape')
            info.external_attr = 0o100644 << 16
            z.writestr(info, b'x')
        expected = {'../escape': dict(bytes=1, sha256=gate.digest(b'x'))}
        with self.assertRaisesRegex(ValueError, 'path or type'):
            gate.extract_exact(archive, self.root / 'bad', expected)
        self.assertFalse((self.root / 'escape').exists())

    def test_shared_manifest_override_and_unknown_member(self):
        manifest = self.root / 'members.json'
        manifest.write_text(json.dumps(dict(countedFiles=[
            dict(path='model', bytes=1, sha256='parent', role='model')])) )
        replacement = dict(path='changed', bytes=2, sha256='treatment')
        plan = dict(member_manifest='members.json', baseline_root='base',
                    overrides={'P': {}, 'D': {'model': replacement}})
        with patch.object(gate, 'ROOT', self.root):
            self.assertEqual(gate.member_rows(plan, 'P')[0]['path'], 'base/model')
            self.assertEqual(gate.member_rows(plan, 'D')[0],
                             dict(replacement, member='model', role='model'))
            plan['overrides']['D']['unknown'] = replacement
            with self.assertRaisesRegex(ValueError, 'unknown package member'):
                gate.member_rows(plan, 'D')


if __name__ == '__main__':
    unittest.main()
