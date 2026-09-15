import io
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile

from tools.fx2_trim_confirm1m_v1 import members, source_zip, ROOT


class Tests(unittest.TestCase):
    def test_frozen_delivery_is_exactly_reconstructible(self):
        root = ROOT / 'results/fx2_expert_release250k_v3'
        with tempfile.TemporaryDirectory(dir='/run/user/1000') as tmp:
            for name in ['original-source.zip', 'P-source.zip']:
                data = (root / name).read_bytes()
                target = Path(tmp) / name
                source_zip(target, members(data))
                self.assertEqual(target.read_bytes(), data)

    def test_only_the_declared_frozen_sources_differ(self):
        root = ROOT / 'results/fx2_expert_release250k_v3'
        p = members((root / 'original-source.zip').read_bytes())
        d = members((root / 'P-source.zip').read_bytes())
        self.assertEqual(set(d) - set(p), set())
        self.assertEqual(set(p) - set(d), {
            'src/mixer/lstm-layer.h', 'src/mixer/lstm-layer.hpp',
            'src/mixer/lstm.h', 'src/mixer/lstm.hpp'})
        self.assertEqual({n for n in d if d[n] != p[n]}, {
            'makefile', 'src/coder/decoder.cpp', 'src/coder/encoder.cpp',
            'src/mixer/byte-mixer.cpp', 'src/mixer/byte-mixer.h',
            'src/predictor.cpp', 'src/predictor.h', 'src/runner.cpp'})
        for n in ['models/6m-q4-fp32.tfwc2', 'dictionary/english.dic', 'LICENSE']:
            self.assertEqual(p[n], d[n])
        self.assertIn(b'if (!transformer_) Fail', d['src/predictor.cpp'])
        self.assertIn(b'#ifdef GAMMA_EXPERT_RELEASE', d['src/predictor.cpp'])

    def test_aliased_or_nonregular_members_are_rejected(self):
        cases = ['../escape', '/absolute', 'x/../escape', './alias', 'dir/']
        for name in cases:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w') as z: z.writestr(name, b'bad')
            with self.subTest(name=name), self.assertRaises(ValueError): members(buf.getvalue())
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as z:
            info = zipfile.ZipInfo('link')
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            z.writestr(info, '../target')
        with self.assertRaises(ValueError): members(buf.getvalue())


if __name__ == '__main__': unittest.main()
