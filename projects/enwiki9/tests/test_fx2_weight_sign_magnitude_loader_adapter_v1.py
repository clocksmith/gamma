"""Source adapter checks only; native parity requires separately bounded execution."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch as mock_patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import fx2_weight_sign_magnitude_loader_v1 as loader

PARENT = ROOT / 'operations/provenance/fx2_adaptive_package_fixture_v1/bundle/package/cpp_infer/src'


class AdapterTests(unittest.TestCase):
    def test_authenticated_sources_deterministic(self):
        for kind, name, digest in (
            ('loader', 'weights_io_compressed.cpp', loader.LOADER_SHA256),
            ('dispatch', 'opt/arena_build.cpp', loader.DISPATCH_SHA256),
        ):
            with self.subTest(kind=kind):
                source = (PARENT / name).read_bytes()
                self.assertEqual(hashlib.sha256(source).hexdigest(), digest)
                self.assertEqual(loader.patch(source, kind), loader.patch(source, kind))
                self.assertIn(b'GFX2SMG1', loader.patch(source, kind))
                self.assertEqual(hashlib.sha256((PARENT / name).read_bytes()).hexdigest(), digest)

    def test_changed_parent_rejected(self):
        for kind in ('loader', 'dispatch'):
            with self.assertRaisesRegex(ValueError, 'parent differs'):
                loader.patch(b'changed', kind)
        with self.assertRaisesRegex(ValueError, 'unknown'):
            loader.patch(b'', 'unknown')

    def test_existing_output_preserved(self):
        # No codec/model execution; ordinary source-fixture temporary directory.
        with tempfile.TemporaryDirectory(dir=ROOT / 'results') as temporary:
            output = Path(temporary) / 'sealed.cpp'
            output.write_bytes(b'sealed')
            args = ['loader', '--source', str(PARENT / 'weights_io_compressed.cpp'),
                    '--output', str(output)]
            with mock_patch.object(sys, 'argv', args):
                with self.assertRaises(FileExistsError):
                    loader.main()
            self.assertEqual(output.read_bytes(), b'sealed')

    def test_nonunique_anchor_rejected(self):
        for source in ('absent', 'old old'):
            with self.assertRaisesRegex(ValueError, 'not unique'):
                loader.replace_once(source, 'old', 'new')


if __name__ == '__main__':
    unittest.main()
