import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from projects.enwiki9.tools import fx2_residual_ratio_fixture50051_q0_v2 as gate


class SyntheticNativeAdapter:
    def __init__(self,g,arm):
        self.g,self.arm,self.calls=g,arm,0
    def phase(self,name,data,decode=False):
        command=[sys.executable,'-c',
            'import os,sys,zlib; print(os.getpid(),file=sys.stderr); '
            'sys.stdout.buffer.write(zlib.'+('decompress' if decode else 'compress')+'(sys.stdin.buffer.read()))']
        result=subprocess.run(command,input=data,capture_output=True,check=True,timeout=20)
        self.g.pids.append(int(result.stderr))
        suffix='.raw' if decode else '.cmix'
        (self.g.work/(self.arm+'-'+name+suffix)).write_bytes(result.stdout)
        return result.stdout
    def compress(self,data):
        name='encode' if self.calls==0 else 'repeat';self.calls+=1
        return self.phase(name,data)
    def decompress(self,data):return self.phase('decode',data,True)


class DispatchTests(unittest.TestCase):
    def test_native_module_dispatch_retains_three_fresh_process_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);work=root/'work';(work/'prof_input').mkdir(parents=True)
            raw=bytes(range(256))*3+b'<page>same same</page>\x00\xff'
            (work/'prof_input/input').write_bytes(raw)
            g=SimpleNamespace(result=root,work=work,pids=[])
            g.write=lambda path,value:(root/path).write_text(json.dumps(value))
            # Registration identity is metadata only; codec bytes come from the
            # supplied adapter, which independently launches each native phase.
            with patch.object(gate,'Codec',SyntheticNativeAdapter),patch.object(gate,'ID','fx2_residual_ratio_fixture50051_q0_v1'):
                result=gate.run_native_arm(g,'D',[('synthetic source',12)],{'complete_submission_package':False})
            self.assertTrue(result['roundtrip_ok'])
            self.assertTrue(result['determinism']['single_host_byte_equal'])
            self.assertEqual(len(set(g.pids)),3)
            self.assertEqual(result['arm'],'D')
            self.assertEqual((root/'D/restored.bin').read_bytes(),raw)
            self.assertEqual((root/'D/archive.bin').read_bytes(),(root/'D/repeat.bin').read_bytes())
            self.assertEqual(json.loads((root/'D/result.json').read_text())['arm'],'D')


if __name__=='__main__':unittest.main()
