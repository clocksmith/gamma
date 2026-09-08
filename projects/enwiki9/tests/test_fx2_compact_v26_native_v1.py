import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name,ROOT/'tools'/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adapter = load('fx2_compact_v26_native_adapter_v1')
runner = load('fx2_compact_v26_fixture50051_q0_v1')


class AdapterTests(unittest.TestCase):
    def test_exact_materialized_header_and_pinned_sources(self):
        actual = adapter.build_adapter()
        recorded = json.loads((ROOT/runner.ADAPTER).read_text())
        self.assertEqual(actual,recorded)
        rows = {r['source_path']:r for r in actual['files']}
        for path,row in rows.items():
            text = (ROOT/adapter.PARENT/'work'/path).read_text()
            for change in row['replacements']:
                self.assertEqual(text.count(change['before']),1)
                text = text.replace(change['before'],change['after'])
            self.assertEqual(adapter.digest(text.encode()),row['patched_sha256'])
        self.assertNotIn('src/models/fxcmv1.cpp',rows)
        self.assertNotIn('cpp_infer/src/opt/model_opt.cpp',rows)

    def test_changed_native_preimage_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            path=root/adapter.PARENT/'work/src/predictor.h'
            path.parent.mkdir(parents=True)
            path.write_text('changed')
            with self.assertRaisesRegex(ValueError,'preimage'):
                adapter.build_adapter(root)

    def test_activation_including_carriage_return(self):
        for arm,n in [('P',431),('K',431),('D',403)]:
            runner.activation(f'progress\rGamma FXCM arm={arm} outputs={n}\n'.encode(),arm)

    def test_wrong_missing_or_duplicate_activation_is_rejected(self):
        for value in [b'',b'Gamma FXCM arm=D outputs=431\n',
                      b'Gamma FXCM arm=P outputs=403\n',
                      b'Gamma FXCM arm=D outputs=403\n'*2]:
            with self.assertRaisesRegex(ValueError,'activation'):
                runner.activation(value,'D')

    def test_repeat_comparison_finds_first_divergence(self):
        with tempfile.TemporaryDirectory() as directory:
            a,b=Path(directory)/'a',Path(directory)/'b'
            a.write_bytes(b'abc');b.write_bytes(b'abx')
            with self.assertRaisesRegex(ValueError,'byte 2'):
                runner.exact(a,b)
            b.write_bytes(b'ab')
            with self.assertRaisesRegex(ValueError,'length'):
                runner.exact(a,b)
            b.write_bytes(b'abc');runner.exact(a,b)


if __name__=='__main__':
    unittest.main()
