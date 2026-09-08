import hashlib
from pathlib import Path
import tempfile
import unittest

from projects.enwiki9.tools import fx2_residual_ratio_native_adapter_v1 as adapter


class NativeAdapterTests(unittest.TestCase):
    def test_exact_source_adaptation_preserves_rounding(self):
        spec=adapter.build_adapter()
        for row in spec['files']:
            original=(adapter.PARENT/row['source_path']).read_text();text=original
            for change in row['replacements']:
                self.assertEqual(text.count(change['before']),1)
                text=text.replace(change['before'],change['after'])
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),row['patched_sha256'])
            if row['source_path'].endswith('.cpp'):
                first=original.index('uint16_t FloatToHalf(');last=original.index('// The encoded article separator')
                self.assertIn(original[first:last],text)
                self.assertIn('if (gamma_ratio_enabled_)',text)
                self.assertIn('GammaRatioAudit(\'O\')',text)
                self.assertIn('GammaRatioAudit(\'P\')',text)

    def test_changed_preimage_fails_without_writes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'src').mkdir()
            for name in adapter.EXPECTED:(root/name).write_bytes((adapter.PARENT/name).read_bytes())
            path=root/'src/predictor.cpp';path.write_bytes(path.read_bytes()+b'\n')
            before=path.read_bytes()
            with self.assertRaises(ValueError):adapter.build_adapter(root)
            self.assertEqual(path.read_bytes(),before)

    def test_added_component_hash_is_bound(self):
        row=adapter.build_adapter()['added_files'][0]
        raw=(adapter.ROOT/row['source']['path']).read_bytes()
        self.assertEqual(row['source']['sha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(row['source']['bytes'],len(raw))
        self.assertEqual(row['target'],'src/gamma-residual-ratio.h')


if __name__=='__main__':unittest.main()
