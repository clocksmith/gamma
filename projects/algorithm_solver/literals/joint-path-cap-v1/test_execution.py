"""Focused new wrapper behavior; supplied fixtures and public receipt validation."""
import copy
import hashlib
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import binding as b
import production
import make_contract
import report
import test_report


class ExecutionTests(unittest.TestCase):
    def test_production_reconciles_all_historical_proofs(self):
        with tempfile.TemporaryDirectory() as d:
            f=test_report.fixture(Path(d));c=f.config
            p,geometry=production.execute(f.inputs,c['old_arms']['R'],c['parent50_arms']['R'],c['parent53_arms']['R'],c['parent57_arms']['R'])
            report.exact(report.shaped(p),f.production['arms'][0]['proof']);report.exact(geometry,f.inputs['geometry'])
            bad=copy.deepcopy(c['parent57_arms']['R']);bad['scientific_proof_sha256']='0'*64
            with self.assertRaises(AssertionError):production.execute(f.inputs,c['old_arms']['R'],c['parent50_arms']['R'],c['parent53_arms']['R'],bad)

    def test_reader_root_allowlist_hash_limit_and_strict_json(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);rel='safe.json';path=root/rel;path.write_text('{"a":1}')
            c={'active':True,'work':str(root),'private_files':{rel:b.sha(path)}}
            with patch.object(b,'WORK',str(root)):
                self.assertEqual(b.parse(b.checked_bytes(c,root,rel)),{'a':1})
                with patch.object(Path,'open',side_effect=AssertionError('must not open')) as opened:
                    with self.assertRaises(AssertionError):b.checked_bytes(c,root/'elsewhere',rel)
                    with self.assertRaises(AssertionError):b.checked_bytes(c,root,'other.json')
                    opened.assert_not_called()
                with patch.object(b,'MAX_BYTES',2):
                    with self.assertRaises(AssertionError):b.checked_bytes(c,root,rel)
                c['private_files'][rel]='0'*64
                with self.assertRaises(AssertionError):b.checked_bytes(c,root,rel)
            for text in ('{"a":1,"a":2}','{"a":NaN}'):
                with self.assertRaises((AssertionError,ValueError)):b.parse(text)

    def test_actual_public_synthetic_acceptance_and_rejected_status(self):
        # Accepted invented public receipts only; build() is never invoked.
        spec=b.read(b.HERE/'synthetic-spec.json');result=b.read(b.HERE/'synthetic-results.json');sup=b.read(b.HERE/'synthetic-supervisor.json')
        h=b.sha(b.HERE/'synthetic-spec.json');make_contract.check_synthetic_receipts(spec,result,sup,h)
        for kind in ('complete','bool_exit','oracle'):
            r,s=copy.deepcopy(result),copy.deepcopy(sup)
            if kind=='complete':r['complete']=False
            elif kind=='bool_exit':s['exit_code']=False
            else:r['oracle_tests']+=1
            with self.assertRaises(AssertionError):make_contract.check_synthetic_receipts(spec,r,s,h)


if __name__=='__main__':unittest.main()
