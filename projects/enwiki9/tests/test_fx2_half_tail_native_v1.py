"""Check source isolation, observation framing, and matched native activation."""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import fx2_half_tail_fixture50051_q0_v1 as runner
from tools import fx2_half_tail_native_adapter_v1 as adapter


class HalfNativeTests(unittest.TestCase):
    def test_adapter_preserves_upstream_conversion_and_model(self):
        value=adapter.build_adapter()
        self.assertEqual(value,json.loads((ROOT/runner.ADAPTER).read_text()))
        self.assertEqual({r['source_path'] for r in value['files']},{'src/predictor.cpp','src/predictor.h'})
        for row in value['files']:
            text=(adapter.PARENT/row['source_path']).read_text()
            for change in row['replacements']:
                self.assertEqual(text.count(change['before']),1)
                text=text.replace(change['before'],change['after'])
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),row['patched_sha256'])
            self.assertNotIn('fxcm_v26',text)
            if row['source_path'].endswith('.cpp'):
                self.assertIn('112 - e',text)
                body=text.split('void Predictor::TransformerByteUpdate() {',1)[1].split('\n}\n',1)[0]
                self.assertLess(body.index('gamma_half_audit_.prior'),body.index('transformer_->step('))
                self.assertLess(body.index('gamma_half_audit_.output'),body.index('if (!(probs_scratch_[i] >= 1e-6f))'))

    def test_changed_parent_and_engine_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            parent=Path(folder);(parent/'src').mkdir()
            (parent/'src/predictor.h').write_text('changed')
            with self.assertRaisesRegex(ValueError,'preimage'):adapter.build_adapter(parent)
        with patch.object(runner,'ENGINE_SHA','0'*64):
            with self.assertRaisesRegex(ValueError,'engine source changed'):runner.load_engine()

    def test_activation_requires_complete_original_model(self):
        engine=runner.bind(runner.load_engine())
        for arm in 'PKD':
            good=f'Gamma FXCM arm={arm} outputs=431\nGamma half arm={arm} rows=32478 subnormal=10 changes=3\n'.encode()
            engine.activation(good,arm)
            for bad in (good+good,good.replace(b'431',b'403'),good.replace(b'32478',b'32477'),good.split(b'Gamma half')[0]):
                with self.assertRaises(Exception):engine.activation(bad,arm)

    def test_materializer_never_switches_model_or_makefile(self):
        engine=runner.bind(runner.load_engine())
        with tempfile.TemporaryDirectory() as folder:
            class Gate:
                work=Path(folder)
                buffers={runner.ADAPTER:json.dumps({'added_files':[]}).encode()}
                def copy(self,source,target):
                    target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_text('fxcmv1.h fxcmv1.cpp fxcmv1.o' if target.name=='makefile' else 'fixture')
                def adapter(self,*args):pass
            package={'source_members':[{'path':engine.PARENT+'work/makefile'}],'runtime_members':[]}
            for arm in 'PKD':
                target=engine.materialize(Gate(),arm,package)
                self.assertEqual((target/'makefile').read_text(),'fxcmv1.h fxcmv1.cpp fxcmv1.o')
            self.assertEqual(engine.COMPACT,'')

    def test_native_trace_and_corruption(self):
        binary=ROOT/'results/fx2_half_tail_native_v1/unit02/fixture'
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'trace'
            proc=subprocess.run([str(binary)],env={**os.environ,'GAMMA_FX2_HALF_TRACE':str(path)},capture_output=True,timeout=10)
            self.assertEqual(proc.returncode,0,proc.stderr)
            runner.validate_half_trace(path,1)
            good=path.read_bytes()
            self.assertEqual(good[:11],b'I'+struct.pack('<HQ',205,0))
            self.assertEqual(good[421:432],b'O'+struct.pack('<HQ',205,0))
            self.assertEqual(good[11:421],struct.pack('<205H',*([0x3c00]*205)))
            for data in (good[:-1],good+b'x',b'X'+good[1:],good[:3]+b'\x01'+good[4:]):
                path.write_bytes(data)
                with self.assertRaises(ValueError):runner.validate_half_trace(path,1)
            path.write_bytes(good)
            other=Path(folder)/'other';other.write_bytes(good[:20]+bytes([good[20]^1])+good[21:])
            with self.assertRaisesRegex(ValueError,'byte 20'):runner.load_engine().exact(path,other)


if __name__=='__main__':unittest.main()
