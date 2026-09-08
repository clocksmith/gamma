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
from lib.wrt_support_v1 import WrtSupport
from tools import fx2_wrt_support_fixture50051_q0_v1 as runner
from tools.fx2_wrt_support_native_adapter_v1 import build,PARENT


class NativeTests(unittest.TestCase):
    def test_all_code_shapes_match_python(self):
        data=bytearray([7])
        for index in range(44880):
            if index<80:data.append(128+index)
            elif index<3920:
                v=index-80;data.extend([208+v//80,128+v%80])
            else:
                v=index-3920;data.extend([240+v//2560,208+(v//80)%32,128+v%80])
        for b in range(256):data.extend([12,b])
        binary=ROOT/'results/wrt_support_native_v1/unit01/probe'
        actual=subprocess.run([str(binary)],input=data,capture_output=True,timeout=15)
        self.assertEqual(actual.returncode,0,actual.stderr)
        names=['mode','neutral','short','long','third','escape','disabled']
        s=WrtSupport();expected=bytearray()
        for b in data:
            for shift in range(7,-1,-1):
                f=s.forced();expected.extend([names.index(s.phase),s.prefix,0 if f is None else f+1]);s.observe((b>>shift)&1)
        s.finish();self.assertEqual(actual.stdout,expected)

    def test_native_audit_and_projection(self):
        data=b'\x07\xd0\x80\xff\xef\xcf\x0c\xfftext'
        s=WrtSupport();expected=bytearray()
        for b in data:
            for shift in range(7,-1,-1):
                f=s.forced();q=12345 if f is None else 65535 if f else 1
                expected.extend(struct.pack('<H',q));s.observe((b>>shift)&1)
        binary=ROOT/'results/wrt_support_native_v1/unit01/probe'
        traces=[]
        with tempfile.TemporaryDirectory() as folder:
            for arm in range(3):
                path=Path(folder)/str(arm)
                p=subprocess.run([str(binary),str(arm)],input=data,capture_output=True,timeout=10,env={**os.environ,'GAMMA_FX2_WRT_TRACE':str(path)})
                self.assertEqual(p.returncode,0,p.stderr)
                self.assertEqual(p.stdout,expected if arm==2 else struct.pack('<H',12345)*(len(data)*8))
                traces.append(path.read_bytes())
            self.assertEqual(len(traces[0]),len(data)*8*16)
            self.assertEqual(traces[0],traces[1]);self.assertEqual(traces[0],traces[2])

    def test_exact_source_composition_preserves_model_calls(self):
        adapter=build();self.assertEqual(adapter,json.loads((ROOT/runner.ADAPTER).read_text()))
        self.assertEqual({r['source_path'] for r in adapter['files']},{'src/coder/encoder.cpp','src/coder/decoder.cpp'})
        for row in adapter['files']:
            text=(PARENT/row['source_path']).read_text()
            for change in row['replacements']:text=text.replace(change['before'],change['after'])
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),row['patched_sha256'])
            self.assertEqual(text.count('p_->Predict()'),1);self.assertEqual(text.count('p_->Perceive(bit)'),1)
            self.assertLess(text.index('audit().project'),text.index('audit().observe'))

    def test_activation_and_engine_identity(self):
        engine=runner.bind(runner.load_engine())
        for arm in 'PKD':
            good=f'Gamma WRT arm={arm} bits=259824 forced=7994 changes=7994\n'.encode();engine.activation(good,arm)
            for bad in (good+good,good.replace(b'259824',b'259823'),b''):
                with self.assertRaises(Exception):engine.activation(bad,arm)
        with patch.object(runner,'ENGINE_SHA','0'*64):
            with self.assertRaises(ValueError):runner.load_engine()


if __name__=='__main__':unittest.main()
