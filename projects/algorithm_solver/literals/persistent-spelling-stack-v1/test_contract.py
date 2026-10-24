"""Public lineage and exact activation checks; no private carrier access."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch
import common as c
import make_contract as m

class ContractTests(unittest.TestCase):
    def test_public_parent_authority_and_no_private_reads(self):
        read=c.read;hashfile=c.hashfile;lit=c.LIT.resolve();seen=[]
        def allow(path):
            path=Path(path).resolve()
            # Runtime files are separately hash-checked. JSON authority reads
            # must stay strictly under the public repository literal directory.
            self.assertTrue(path.is_relative_to(lit),str(path));seen.append(path)
        def reading(path):allow(path);return read(path)
        with patch.object(c,'read',side_effect=reading):parent,pins,paths=m.parent_authority()
        self.assertEqual(len(parent['source_qualification']),400)
        self.assertEqual(parent['limits']['worker_seconds'],1800)
        self.assertTrue(set(parent['code_hashes'])<=set(pins['code_hashes']))
        self.assertEqual(len(paths),5);self.assertGreater(len(seen),0)
    def test_exact_activation_and_inherited_pin_drift(self):
        pending={'active':False,'source_bound':True,'parser':{'x':'bound'}}
        got=m.activate(copy.deepcopy(pending),pending)
        self.assertTrue(got['active']);self.assertFalse(pending['active'])
        altered=copy.deepcopy(pending);altered['parser']['x']='changed'
        with self.assertRaises(AssertionError):m.activate(altered,pending)
        with self.assertRaises(AssertionError):m.merge_pins({'same':'old'},{'same':'new'})

if __name__=='__main__':unittest.main()
