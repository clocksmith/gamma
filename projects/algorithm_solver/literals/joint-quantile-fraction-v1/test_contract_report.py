import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import common
import make_contract
import report
import supervise


class ContractReportTests(unittest.TestCase):
    def test_activation_rejects_any_pending_drift(self):
        pending={'active':False,'code_hashes':{'x':'a'},'limits':{'n':10}}
        active=make_contract.activate(copy.deepcopy(pending),pending)
        self.assertTrue(active['active']);self.assertFalse(pending['active'])
        for key,value in (('code_hashes',{'x':'b'}),('limits',{'n':11})):
            current=copy.deepcopy(pending);current[key]=value
            with self.assertRaises(AssertionError):make_contract.activate(current,pending)

    def test_run_and_supervisor_timing_fail_closed(self):
        contract={'limits':{'production_seconds':1200,'cleanup_seconds':10}}
        raw={'complete':True,'validation_loaded':False,'contract_sha256':'hash','seconds':10,
             'arms':[{'cohort':'R','seconds':8},{'cohort':'naming','seconds':9}]}
        sup={'complete':True,'phase':'production','contract_sha256':'hash','elapsed':11,'cleanup_seconds':.1,'returncodes':[0,0]}
        with patch.object(common,'sha',return_value='hash'):
            report.verify_run(raw,contract);report.verify_supervisor(sup,raw,contract)
            for value in (float('nan'),float('inf'),-1,1201):
                bad=copy.deepcopy(raw);bad['seconds']=value
                with self.assertRaises(AssertionError):report.verify_run(bad,contract)
            for value in (float('nan'),float('inf'),-1,1211,9):
                bad=copy.deepcopy(sup);bad['elapsed']=value
                with self.assertRaises(AssertionError):report.verify_supervisor(bad,raw,contract)
            bad=copy.deepcopy(raw);bad['private_debug']='private'
            with self.assertRaises(AssertionError):report.verify_run(bad,contract)

    def test_failure_overwrites_stale_success(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder);(path/'REPORT.md').write_text('SUCCESS OLD')
            report.publish({'complete':False},path)
            self.assertNotIn('SUCCESS OLD',(path/'REPORT.md').read_text())
            self.assertIn('no overall certificate',(path/'REPORT.md').read_text())
            self.assertFalse(json.loads((path/'results.json').read_text())['complete'])

    def test_refused_existing_report_archives_old_success(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);out=root/'output';out.mkdir()
            common.write(root/'contract.json',{'limits':{'report_seconds':1200}})
            (out/'REPORT.md').write_text('OLD SUCCESS')
            common.write(out/'results.json',{'complete':True})
            with patch.object(common,'HERE',root):
                with self.assertRaises(FileExistsError):supervise.main('report',root,out,root)
            self.assertIn('no overall certificate',(out/'REPORT.md').read_text())
            self.assertFalse(json.loads((out/'results.json').read_text())['complete'])
            saved=list(out.glob('previous-*/REPORT.md'))
            self.assertEqual(len(saved),1);self.assertEqual(saved[0].read_text(),'OLD SUCCESS')

    def test_zero_scale_and_floor_are_deterministic(self):
        q={'p':[[0,1,2,3,4,5]]}
        self.assertEqual(common.scaled(q,(1,4)),{'p':[[0,0,0,0,1,1]]})
        self.assertEqual(common.scaled(q,(0,1)),{'p':[[0]*6]})
        with self.assertRaises(AssertionError):common.scaled(q,(3,1))


if __name__=='__main__':unittest.main()
