"""Invented sources only; isolated temporary parents never access research inputs."""
import copy
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import codec
import prototype
import report
import run

HERE=Path(__file__).resolve().parent
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    run.analyze.write(path,value)
sha=lambda path:run.analyze.sha(Path(path).read_bytes())


class PipelineTests(unittest.TestCase):
    def fixture(self,root):
        source=root/'invented-parent';out=root/'output';binding=root/'binding';binding.mkdir()
        texts,nodes,keys,banned,_=prototype.counterexample()
        alltext={**texts,'4':texts['0'].replace('pad=0','pad=1'),'5':texts['3'].replace('pad=0','pad=2')}
        parentq={pid:{'passed':True,'source_sha256':run.analyze.sha(text.encode()),'receipt':{'passed':True,'synthetic':True}} for pid,text in alltext.items()}
        files={'results.json':{'synthetic':True,'source_qualification':parentq},
               'supervisor-receipt.json':{'complete':True,'promotion_allowed':True,'outer_timeout':False},
               'fit/D11/fit-sources.json':texts,'fit/D11/dictionary.json':[k[1:] for k in keys],
               'artifacts/D11/dictionary.json':[k[1:] for k in keys],'artifacts/D11/sources.json':alltext}
        for rel,value in files.items():write(source/rel,value)
        cores=sorted(os.sched_getaffinity(0))[:4]
        decoder={'literal':[str(HERE.parent/'literals.py'),str(HERE.parent/'pass2/working/bitpack.py')],
                 'typed':[str(HERE/'decoder.cjs'),'/usr/share/nodejs/acorn/dist/acorn.js']}
        c={'source_bound':True,'source_run':str(source),'python_version':platform.python_version(),
           'python_bin':sys.executable,'runtime_files':{},'code_hashes':{},
           'all_cores':cores,'cores':[[core] for core in cores],
           'limits':{'address_space_bytes':8589934592,'overall_seconds':30},'search':{'trials':100,'seconds':5},
           'private_files':{rel:sha(source/rel) for rel in files},'source_qualification':parentq,
           'partition':{'dev_fit':[0,1,2,3],'dev_val':[4,5]},'decoder_dependencies':decoder,
           'decoder_bytes':{kind:sum(Path(p).stat().st_size for p in paths) for kind,paths in decoder.items()}}
        write(binding/'contract.json',c)
        return source,out,binding,c

    def test_full_four_worker_flow_then_corrupt_report_refuses_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source,out,binding,c=self.fixture(root)
            driver=root/'synthetic_driver.py'
            driver.write_text('import sys\nfrom pathlib import Path\nsys.path.insert(0,'+repr(str(HERE))+')\nimport run\n'
                "if __name__=='__main__':\n    run.HERE=Path("+repr(str(binding))+')\n'
                '    original_read=run.read\n'
                '    def observed_read(path):\n'
                '        if str(path).endswith("artifacts/D11/sources.json"):\n'
                '            assert (Path('+repr(str(out))+')/"all-fit-sealed.json").exists()\n'
                '        return original_read(path)\n'
                '    run.read=observed_read\n'
                '    run.guarded_main(Path('+repr(str(source))+'),Path('+repr(str(out))+'))\n')
            proc=subprocess.run([sys.executable,'-B',str(driver)],env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),
                                capture_output=True,text=True,timeout=30)
            self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
            self.assertTrue(run.read(out/'status.json')['complete'])
            write(out/'supervisor-receipt.json',{'complete':True,'promotion_allowed':True,'outer_timeout':False})
            def synthetic_parent(root,c):
                q=run.read(root/'results.json')['source_qualification']
                self.assertEqual(q,c['source_qualification'])
                self.assertTrue(all(r['passed'] and r['receipt']['passed'] for r in q.values()))
            with patch.object(report,'HERE',binding),patch.object(report,'verify_parent',synthetic_parent):
                got=report.main(out)
                self.assertNotEqual(got.get('verdict_available'),False,got)
                self.assertEqual(len(got['arms']),5)
                self.assertTrue(got['predictions']['S1_all_views_decode_and_qualify']['observed'])
                self.assertFalse(got['flat_M1_promotion_allowed'])
                original=(out/'TB/packets/4.bin').read_bytes()
                (out/'TB/packets/4.bin').write_bytes(original[:-1]+bytes([original[-1]^1]))
                bad=report.main(out)
                self.assertFalse(bad['verdict_available'])
                self.assertIsNone(bad['selected_structured_candidate'])
                (out/'TB/packets/4.bin').write_bytes(original)
                write(out/'failure.json',{'phase':'validation','error_type':'synthetic_failure'})
                self.assertFalse(report.main(out)['verdict_available'])

    def test_worker_exception_preserves_phase_and_partial_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'out'
            def failing(source,folder):
                folder.mkdir();write(folder/'status.json',{'phase':'fit','complete':False})
                write(folder/'partial.json',{'synthetic':True});raise RuntimeError('invented worker error')
            with patch.object(run,'main',failing):
                with self.assertRaises(RuntimeError):run.guarded_main(Path(tmp)/'source',out)
            self.assertEqual(run.read(out/'failure.json')['phase'],'fit')
            self.assertFalse(run.read(out/'status.json')['complete'])
            self.assertTrue((out/'partial.json').exists())

    def test_supervisor_timeout_keeps_partial_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);stub=root/'stub';stub.mkdir();out=root/'output';core=min(os.sched_getaffinity(0))
            write(stub/'contract.json',{'source_bound':True,'source_run':str(root/'invented'),
                'python_bin':sys.executable,'all_cores':[core],'limits':{'overall_seconds':.3}})
            (stub/'run.py').write_text('import argparse,json,time\nfrom pathlib import Path\np=argparse.ArgumentParser();p.add_argument("--source-run");p.add_argument("--output");a=p.parse_args();out=Path(a.output);out.mkdir();(out/"status.json").write_text(json.dumps({"phase":"fit","complete":False}));(out/"partial.txt").write_text("invented");time.sleep(20)\n')
            driver=root/'launch_driver.py';driver.write_text('import sys\nfrom pathlib import Path\nsys.path.insert(0,'+repr(str(HERE))+')\nimport launch\nlaunch.HERE=Path('+repr(str(stub))+')\nlaunch.main()\n')
            proc=subprocess.run([sys.executable,'-B',str(driver),'--source-run',str(root/'invented'),'--output',str(out)],capture_output=True,text=True,timeout=5)
            self.assertEqual(proc.returncode,1,proc.stdout+proc.stderr)
            self.assertTrue(run.read(out/'supervisor-receipt.json')['outer_timeout'])
            self.assertEqual(run.read(out/'failure.json')['phase'],'fit')
            self.assertTrue((out/'partial.txt').exists())


if __name__=='__main__':unittest.main()
