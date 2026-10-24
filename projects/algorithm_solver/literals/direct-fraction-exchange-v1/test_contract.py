import copy
import json
import os
from pathlib import Path
import resource
import signal
import tempfile
import time
import unittest
from unittest.mock import patch

import common as c
import make_contract
import run


class ContractTests(unittest.TestCase):
    def test_exact_pending_activation_only(self):
        pending={'active':False,'code_hashes':{'x':'a'},'limits':{'seconds':1}}
        active=make_contract.activate(copy.deepcopy(pending),pending)
        self.assertTrue(active['active']);self.assertFalse(pending['active'])
        for key,value in (('code_hashes',{'x':'b'}),('limits',{'seconds':2}),('active',True)):
            changed=copy.deepcopy(pending);changed[key]=value
            with self.assertRaises(AssertionError):make_contract.activate(changed,pending)

    def test_inactive_loader_never_opens_input(self):
        with patch.object(Path,'read_text',side_effect=AssertionError('unexpected file read')) as read:
            with self.assertRaises(AssertionError):c.load_cohort({'active':False},Path('/invented-never-open'),'R')
            read.assert_not_called()

    def worker_fixture(self,root):
        contract={'active':True,'limits':{'production_seconds':1200,'address_space_bytes':8*1024**3,
                                         'arm_cores':{'R':[6],'naming':[7]}}}
        c.write(root/'contract.json',contract);output=root/'output';output.mkdir();return output

    def test_runtime_guards_precede_loader_and_failure_is_retained(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);output=self.worker_fixture(root)
            def fake_load(*args):
                self.assertEqual(os.sched_getaffinity(0),{6})
                self.assertEqual(resource.getrlimit(resource.RLIMIT_AS),(8*1024**3,)*2)
                self.assertGreater(signal.getitimer(signal.ITIMER_REAL)[0],0)
                raise ValueError('invented setup failure')
            with patch.object(c,'HERE',root),patch.object(c,'check_contract'),patch.object(c,'load_cohort',side_effect=fake_load):
                with self.assertRaises(ValueError):run.arm('R',root,output,time.monotonic()+2)
            failure=json.loads((output/'R/failure.json').read_text())
            self.assertEqual(failure['phase'],'input_pool_replay');self.assertEqual(failure['exception'],'ValueError')
            self.assertFalse(failure['partial_witnesses_promoted'])
            self.assertFalse((output/'R/results.json').exists())
            self.assertEqual(signal.getitimer(signal.ITIMER_REAL)[0],0)

    def test_whole_worker_timeout_interrupts_setup(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);output=self.worker_fixture(root)
            with patch.object(c,'HERE',root),patch.object(c,'check_contract'),patch.object(c,'load_cohort',side_effect=lambda *a:time.sleep(2)):
                with self.assertRaises(run.WholeJobTimeout):run.arm('R',root,output,time.monotonic()+.05)
            failure=json.loads((output/'R/failure.json').read_text())
            self.assertEqual(failure['exception'],'WholeJobTimeout');self.assertFalse(failure['complete'])


if __name__=='__main__':unittest.main()
