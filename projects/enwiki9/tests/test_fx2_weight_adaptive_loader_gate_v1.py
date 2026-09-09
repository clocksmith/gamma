"""Test build-phase limits and terminal handling without model access."""
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from fx2_weight_adaptive_loader_gate_v1 import phase


class PhaseTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=os.environ['FX2_LOADER_TMP'])
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);(self.root/'tmp').mkdir()
        self.bounds=dict(phase_elapsed_seconds=5,address_space_bytes=536870912,
                         cpu_seconds_per_phase=5,per_file_bytes=33554432,scratch_bytes=33554432)

    def test_phase_output_and_owned_scratch(self):
        result=phase(self.root,'success',[sys.executable,'-c','import os; print(os.environ["TMPDIR"])'],self.bounds,time.monotonic()+10)
        self.assertEqual(result.strip(),str((self.root/'tmp').resolve()))
        self.assertTrue((self.root/'commands.jsonl').exists())

    def test_nonzero_phase_rejected_and_retained(self):
        with self.assertRaisesRegex(ValueError,'phase failed'):
            phase(self.root,'failure',[sys.executable,'-c','raise SystemExit(7)'],self.bounds,time.monotonic()+10)
        self.assertIn('"returncode": 7',(self.root/'commands.jsonl').read_text())

    def test_timeout_terminates_process_group(self):
        self.bounds['phase_elapsed_seconds']=0.5
        script='import subprocess; p=subprocess.Popen(["sleep","60"]); print(p.pid,flush=True); p.wait()'
        with self.assertRaisesRegex(TimeoutError,'phase elapsed stop'):
            phase(self.root,'timeout',[sys.executable,'-c',script],self.bounds,time.monotonic()+10)
        pid=int((self.root/'timeout.stdout').read_text())
        for _ in range(20):
            try:state=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[0]
            except FileNotFoundError:return
            if state=='Z':return
            time.sleep(0.01)
        self.fail('timed-out descendant remains live')


if __name__=='__main__':unittest.main()
