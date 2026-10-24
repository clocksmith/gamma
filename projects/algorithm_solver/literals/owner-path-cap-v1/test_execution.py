"""Invented original-nine-file adapter and bounded worker integration checks."""
import copy
import hashlib
import io
import json
import os
import signal
from pathlib import Path
import tempfile
import time
import types
import unittest
from unittest.mock import patch
import numpy as np
import binding as b
import production
import caps
import run
import report
import independent
import make_contract
from test_report import fixture

tighten=caps.parent

def supplied():
    texts = {'0': 'abcd', '1': 'aefg'}; banned = set(texts.values())
    pool = sorted(set(''.join(texts.values())) | {'z'}); q = [0]*8
    index = tighten.full.Index(texts, banned)
    shape = {'source_characters': 8, 'full_groups': len(index.groups),
             'full_distinct_entries': index.distinct_allowed_entries,
             'exact_ban_occurrences': sum(len(s) for rows in index.banned_ends.values() for s in rows)}
    cert = {'denominator': 7, 'per_program_path_numerators': [252, 252],
            'relaxed_paths_numerator': 504, 'top_capacity_numerator': 0,
            'numerator': 504, 'integer_lower_bound': 72}
    return {'texts': texts, 'banned': banned, 'pool': pool, 'q': q, 'seed': pool,
            'alphabet': pool, 'denominator': 7, 'source_hashes': tighten.source_hashes(texts),
            'parent_certificate': cert, 'geometry': shape, 'bindings': {}}, {
            'shared_learned_entries': 0, 'seed_extra_entries': 0, 'occurrences': 8,
            'pool_entries': len(pool), 'maximum_entry_length': 1,
            'seed_extras_sha256': hashlib.sha256(b'[]').hexdigest()}

class ExecutionTests(unittest.TestCase):
    def test_q_signed_64_one_dimension_and_exact_payload(self):
            def encoded(array):
                out = io.BytesIO(); np.save(out, array); return out.getvalue()
            good = encoded(np.asarray([0, 1, 2**61], dtype=np.int64))
            self.assertEqual(b.load_q(good, 3), [0, 1, 2**61])
            cases = [np.asarray([0, 1, 2], dtype=np.uint64), np.asarray([0, 1, 2], dtype=np.int32),
                     np.asarray([0., 1., 2.]), np.asarray([True, False, True]),
                     np.asarray([[0, 1, 2]], dtype=np.int64), np.asarray([0, -1, 2], dtype=np.int64)]
            for array in cases:
                with self.assertRaises(AssertionError): b.load_q(encoded(array), 3)
            with self.assertRaises(AssertionError): b.load_q(good, 2)
            with self.assertRaises(AssertionError): b.load_q(good+b'extra', 3)

    def test_real_pinned_parser_invented_arrow_singleton(self):
            texts = {'a': 'const solve=()=>1;'}
            bans = b.parse_bans(texts, time.monotonic()+10)
            self.assertIn('1', bans); self.assertIn('()=>1', bans)
            self.assertIn(texts['a'], bans)

    def test_inactive_refusal_before_private_loader(self):
            with patch.object(b, 'checked_bytes', side_effect=AssertionError('private read')) as opened:
                with self.assertRaises(AssertionError): b.load_inputs({'active': False}, Path('/unused'), 'R', time.monotonic()+10)
                opened.assert_not_called()

    def test_exact_activation_and_pin_drift(self):
            with tempfile.TemporaryDirectory() as d:
                path = Path(d)/'code.py'; path.write_text('pass\n')
                pending = {'active': False, 'code_hashes': {'code.py': b.sha(path)}, 'runtime_files': {}}
                with patch.object(b, 'LIT', Path(d)):
                    value = make_contract.activate(copy.deepcopy(pending), pending)
                    self.assertIs(value['active'], True); self.assertIs(pending['active'], False)
                    with self.assertRaises(AssertionError): make_contract.activate(pending | {'extra': True}, pending)
                    path.write_text('changed\n')
                    with self.assertRaises(AssertionError): make_contract.activate(pending, pending)

    def test_cohort_loader_opens_only_five_hash_checked_invented_files(self):
            inputs, expected = supplied()
            with tempfile.TemporaryDirectory() as d:
                root = Path(d); paths = {'sources': 'source.json', 'seed': 'seed.json', 'pool': 'pool.json', 'q': 'q.npy'}
                for field, value in (('sources', inputs['texts']), ('seed', inputs['seed']), ('pool', inputs['pool'])):
                    (root/paths[field]).write_text(json.dumps(value))
                np.save(root/paths['q'], np.asarray(inputs['q'], dtype=np.int64))
                cert = inputs['parent_certificate'] | {'q_sha256': b.sha(root/paths['q'])}
                expected.update(fit_source_sha256=b.sha(root/paths['sources']), pool_sha256=b.sha(root/paths['pool']),
                                pool_entries=len(inputs['pool']), maximum_entry_length=1, certificate=cert)
                # Loader's production alphabet is96; use an invented matching
                # patched alphabet here, without weakening the real contract.
                arm = {k: v for k, v in expected.items() if k != 'certificate'} | {
                       'cohort': 'R', 'mode': 'flex256', 'capacity': 256, 'mandatory_entries': 0,
                       'validation_loaded': False, 'optimization': {'certificate': cert}}
                parent = {'contract_sha256': 'parent', 'validation_loaded': False,
                          'arms': [arm, arm | {'cohort': 'naming'}]}
                (root/'old.json').write_text(json.dumps(parent))
                files = {rel: b.sha(root/rel) for rel in [*paths.values(), 'old.json']}
                c = {'active': True, 'cohorts': {'R': paths}, 'old_private_results': 'old.json', 'private_files': files,
                     'old_arms': {'R': expected}, 'parent_contracts': {'28': {'sha256': 'parent'}},
                     'fit_ids': [0, 1], 'source_hashes': {'R': inputs['source_hashes']}, 'denominator': 7,
                     'full_shape': {'R': inputs['geometry']}, 'public_files': {
                        'all-length-fraction-v1/evidence/results.json': 'old-evidence',
                        'length-sensitive-fraction-v1/evidence/results.json': 'full-evidence'}}
                identities = {'source_sha256': files[paths['sources']], 'seed_sha256': files[paths['seed']],
                  'pool_sha256': files[paths['pool']], 'q_sha256': files[paths['q']], 'old_private_results_sha256': files['old.json'],
                  'source_hashes_sha256': b.digest(inputs['source_hashes']), 'bans_sha256': b.digest(sorted(inputs['banned'])),
                  'banned_entries': len(inputs['banned']), 'old_evidence_sha256': 'old-evidence', 'full_evidence_sha256': 'full-evidence'}
                c['parent50_arms'] = {'R': {'bindings_sha256': b.digest(identities),
                                          'banned_set_sha256': b.digest(sorted(inputs['banned']))}}
                checked = b.checked_bytes
                with patch.object(b, 'check_contract'), patch.object(b, 'ALPHABET', inputs['alphabet']), \
                     patch.object(b, 'parse_bans', return_value=inputs['banned']), patch.object(b, 'checked_bytes', wraps=checked) as opened:
                    loaded = b.load_inputs(c, root, 'R', time.monotonic()+10)
                    self.assertEqual(loaded['q'], inputs['q'])
                    self.assertEqual({call.args[2] for call in opened.call_args_list}, set(files))
                    self.assertEqual(opened.call_count, 5)
                    (root/paths['sources']).write_text('changed')
                    with self.assertRaises(AssertionError): b.load_inputs(c, root, 'R', time.monotonic()+10)

    def test_parser_hard_deadline_never_waits(self):
        class Deadline(BaseException):pass
        proc=unittest.mock.Mock();proc.communicate.side_effect=Deadline()
        with patch.object(b.subprocess,'Popen',return_value=proc):
            with self.assertRaises(Deadline):b.parse_bans({'x':'const solve=()=>1;'},time.monotonic()+10)
        proc.kill.assert_called_once();proc.wait.assert_not_called()

    def test_actual_run_to_independent_report_both_cohorts(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=fixture(root);out=root/'actual-run';out.mkdir();replay=root/'actual-report';replay.mkdir()
            original=report.module
            fake=types.SimpleNamespace(check_contract=lambda c:None,load_inputs=lambda *a:copy.deepcopy(f.inputs))
            with patch.object(b,'HERE',root),patch.object(b,'check_contract'),patch.object(b,'load_inputs',return_value=f.inputs),\
                 patch.object(run.os,'sched_setaffinity'),patch.object(run.resource,'setrlimit'):
                for cohort in report.COHORTS:run.arm(cohort,root/'no-private',out,time.monotonic()+30)
            arms=[b.json.loads((out/cohort/'results.json').read_text()) for cohort in report.COHORTS]
            report.write(out/'results.json',{'complete':True,'validation_loaded':False,'contract_sha256':f.contract_hash,'seconds':2.,'arms':arms})
            report.write(out/'supervisor.json',{'complete':True,'phase':'production','contract_sha256':f.contract_hash,'elapsed':2.1,'cleanup_seconds':.01,'returncodes':[0,0]})
            with patch.object(report,'HERE',root),patch.object(report,'module',side_effect=lambda n,p:fake if p.name=='binding.py' else independent),\
                 patch.object(report.os,'sched_setaffinity'),patch.object(report.resource,'setrlimit'):
                for cohort in report.COHORTS:report.worker(cohort,root/'no-private',out,replay,time.monotonic()+30)
                result=report.combine(out,replay,f.config,20.,[0,0])
            self.assertTrue(result['predictions']['P1']);self.assertEqual(len(result['arms']),2)

    def test_synthetic_receipt_completion_clock_and_integer_exit(self):
        spec={'whole_seconds':180,'synthetic_only':True,'private_inputs_opened':False,'input_spec_sha256':'i','oracle_tests':15,
              'inputs':{'fixtures':[{'name':'a'},{'name':'b'}]},'per_process_address_space_bytes':8*1024**3}
        flags={k:True for k in ('complete','independent_all257_agree','historical53_saved_fields_agree',
            'independent_owner_top_identities_agree','independent_base_paired_proofs_agree','all_forward_recurrences_checked')}
        result={'schema':'gamma.owner-path-cap.synthetic-result.v1','complete':True,'synthetic_only':True,'private_inputs_opened':False,
                'phase':'complete','spec_sha256':'s','input_spec_sha256':'i','oracle_tests':15,'seconds':2.,
                'worker_seconds':1.8,'computation_seconds':1.5,'oracle_seconds':.2,'normal_cleanup_seconds':.01,
                'fixtures':[flags|{'name':'a'},flags|{'name':'b'}],'peak_rss_kib':1000,'supervisor_peak_rss_kib':500}
        supervisor={'complete':True,'synthetic_only':True,'spec_sha256':'s','exit_code':0,'seconds':2.1,'normal_cleanup_seconds':.01}
        make_contract.check_synthetic_receipts(spec,result,supervisor,'s')
        for target,key,value in [('s','exit_code',False),('s','seconds',float('nan')),('r','complete',False),
                                 ('r','seconds',3.),('r','normal_cleanup_seconds',11),('r','oracle_tests',True)]:
            a,z=copy.deepcopy(result),copy.deepcopy(supervisor);(a if target=='r' else z)[key]=value
            with self.assertRaises(AssertionError):make_contract.check_synthetic_receipts(spec,a,z,'s')


    def test_public53_authority_rejects_rebound_arithmetic_and_input_drift(self):
        parent=json.loads((b.LIT/'potential-tightening-v1/contract.json').read_text())
        evidence=json.loads((b.LIT/'potential-tightening-v1/evidence/results.json').read_text())
        c=copy.deepcopy(parent)
        c['parent53_contract']={'sha256':b.sha(b.LIT/'potential-tightening-v1/contract.json')}
        c['parent53_arms']={a['cohort']:copy.deepcopy(a) for a in evidence['arms']}
        b.accepted_parent53(c,parent,evidence)
        for kind in ('row','delta','source','pool','incomplete','top'):
            x,z=copy.deepcopy(c),copy.deepcopy(evidence)
            if kind=='row':z['arms'][0]['rows'][3]['charge']+=1
            if kind=='delta':z['arms'][0]['deltas'][3]['charge_reduction']+=1
            if kind=='source':z['arms'][0]['source_identity_sha256']='0'*64
            if kind=='pool':x['private_files'][x['cohorts']['R']['pool']]='0'*64
            if kind=='incomplete':z['complete']=False
            if kind=='top':z['arms'][0]['top_entries_sha256']='0'*64
            x['parent53_arms']={a['cohort']:a for a in z['arms']}
            with self.assertRaises(AssertionError):b.accepted_parent53(x,parent,z)

if __name__=='__main__':unittest.main()
