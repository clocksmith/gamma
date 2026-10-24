"""Inactive metadata boundaries; no actual binder build or parent read."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import common as c
import make_contract as m

class BindingTests(unittest.TestCase):
    def test_absent43_cannot_write_binding(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(c,'LIT',Path(folder)):
                with self.assertRaisesRegex(RuntimeError,'Both independently'):m.build()
            self.assertEqual(list(Path(folder).iterdir()),[])
    def test_actual_public_lineage_distinguishes_D10_from_13_24_43(self):
        c24=c.read(c.LIT/'character-slots-v1/contract.json');c43=c.read(c.LIT/'nonregress24-v1/contract.json')
        old=c.read(c.LIT/'atomic-naming-entry-v1/contract.json')
        optional=next(a for a in c.read(c.LIT/'character-slots-v1/evidence/results.json')['arms'] if a['arm']=='optional')
        q13=next(a for a in c.read(c.LIT/c43['qualification_receipt'])['arms'] if a['arm']=='scope_joint' and a['width']==8)
        got=m.original_source_authority(c24,c43,optional,q13,old['partition'])
        self.assertTrue(any(got[pid]['source_sha256']!=old['source_qualification'][pid]['source_sha256'] for pid in got))
        self.assertTrue(all(got[pid]['source_sha256']==optional['per_problem'][pid]['source_sha256'] for pid in got))
        changed=copy.deepcopy(c43);changed['seed']['private_sha256']['sources.json']='wrong-original-source-carrier'
        with self.assertRaises(AssertionError):m.original_source_authority(c24,changed,optional,q13,old['partition'])
        changed=copy.deepcopy(optional);pid=next(iter(got));changed['per_problem'][pid]['source_sha256']='wrong-source'
        with self.assertRaises(AssertionError):m.original_source_authority(c24,c43,changed,q13,old['partition'])

    def test_exact_activation_only(self):
        pending={'active':False,'source_bound':True,'opaque':'same'}
        got=m.activate(copy.deepcopy(pending),pending)
        self.assertTrue(got['active']);self.assertFalse(pending['active'])
        for current in ({**pending,'opaque':'drift'},{**pending,'source_bound':False}):
            with self.assertRaises(AssertionError):m.activate(current,pending)

if __name__=='__main__':unittest.main()
