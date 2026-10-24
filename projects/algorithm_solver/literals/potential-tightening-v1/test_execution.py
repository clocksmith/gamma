"""Invented adapter, activation and q-shape checks; never private corpus reads."""
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
import tighten
from test_tighten import load50
import run
import make_contract


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


def expected50(inputs):
    proof = load50().Lift(inputs['texts'], inputs['banned'], inputs['pool'], inputs['q'],
        inputs['seed'], inputs['alphabet'], inputs['denominator'],
        old_source_hashes=inputs['source_hashes'], old_banned=inputs['banned']).certificate(256)
    scientific = {k: proof[k] for k in ('denominator','path_numerators','old_charge','old_numerator',
                   'class_counts','top_entries','rows','old_occurrences','occurrence_sha256')}
    return {'complete': True, 'validation_loaded': False,
      'all257_independently_replayed': True, 'old_certificate_independently_replayed': True,
      'suffix_potential_proof_checked': True,
      'bindings_sha256': b.digest(inputs['bindings']), 'source_identity_sha256': b.digest(inputs['source_hashes']),
      'banned_set_sha256': b.digest(sorted(inputs['banned'])), 'parent_certificate_sha256': b.digest(inputs['parent_certificate']),
      'old_occurrence_order_sha256': proof['occurrence_sha256'],
      'old_path_terms_sha256': b.digest([proof['path_numerators'][pid] for pid in sorted(inputs['texts'])]),
      'checked_proof_sha256': tighten.digest(scientific), 'top_entries_sha256': tighten.digest(proof['top_entries']),
      'fit_problems': len(inputs['texts']), 'old_pool_entries': len(inputs['pool']), 'seed_entries': len(inputs['seed']),
      'old_occurrences': len(inputs['q']), 'geometry': inputs['geometry'], 'denominator': inputs['denominator'],
      'path_numerator': sum(proof['path_numerators'].values()), 'old_charge': proof['old_charge'],
      'old_numerator': proof['old_numerator'], 'old_integer_lower_bound': -(-proof['old_numerator']//inputs['denominator']),
      'class_counts': {str(k):v for k,v in proof['class_counts'].items()}, 'rows': proof['rows'],
      'largest_positive_k': max((row['k'] for row in proof['rows'] if row['integer_lower_bound'] > 0), default=None)}


class ExecutionTests(unittest.TestCase):
    def test_synthetic_result_requires_completed_integer_exit_supervisor(self):
        spec=json.loads((b.HERE/'synthetic-spec.json').read_text())
        receipt=json.loads((b.HERE/'synthetic-results.json').read_text())
        supervisor=json.loads((b.HERE/'synthetic-supervisor.json').read_text())
        sha=b.sha(b.HERE/'synthetic-spec.json')
        make_contract.check_synthetic_receipts(spec,receipt,supervisor,sha)
        for kind in ('failed','bool','wrong_spec','late_result','late_supervisor'):
            a,z=copy.deepcopy(receipt),copy.deepcopy(supervisor)
            if kind=='failed':z['complete']=False
            if kind=='bool':z['exit_code']=False
            if kind=='wrong_spec':z['spec_sha256']='0'*64
            if kind=='late_result':a['seconds']=z['seconds']+.01
            if kind=='late_supervisor':z['seconds']=180.01
            with self.subTest(kind=kind),self.assertRaises(AssertionError):make_contract.check_synthetic_receipts(spec,a,z,sha)

    def test_adapter_old_parity_and_full_curve(self):
        inputs, old = supplied(); proof, shape = production.execute(inputs, old, expected50(inputs))
        self.assertEqual(shape, inputs['geometry']); self.assertEqual(len(proof['tightened']['rows']), 257)
        self.assertEqual(proof['tightened']['rows'][0]['integer_lower_bound'], 72)
        self.assertLess(proof['tightened']['rows'][-1]['numerator'], 0)

    def test_adapter_parent_order_geometry_and_extra_corruption(self):
        for key in ('paths', 'charge', 'shape', 'extras'):
            inputs, old = supplied(); prior = expected50(inputs)
            if key == 'paths': inputs['parent_certificate']['per_program_path_numerators'][0] += 1
            if key == 'charge': inputs['parent_certificate']['top_capacity_numerator'] += 1
            if key == 'shape': inputs['geometry']['full_distinct_entries'] += 1
            if key == 'extras': old['seed_extra_entries'] += 1
            with self.assertRaises(AssertionError): production.execute(inputs, old, prior)

    def test_adapter_rejects_rebound50_curve_top_and_bool_counters(self):
        inputs,old=supplied()
        for kind in ('curve','top','proof','order','bool','source'):
            prior=expected50(inputs)
            if kind=='curve':prior['rows'][3]['charge']+=1
            if kind=='top':prior['top_entries_sha256']='0'*64
            if kind=='proof':prior['checked_proof_sha256']='0'*64
            if kind=='order':prior['old_occurrence_order_sha256']='0'*64
            if kind=='bool':prior['old_charge']=False
            if kind=='source':prior['source_identity_sha256']='0'*64
            with self.subTest(kind=kind),self.assertRaises(AssertionError):production.execute(inputs,old,prior)

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

    def test_accepted50_public_metadata_drift_before_private_access(self):
        # Read only already recorded public50; this does not call the53 binder
        # or construct/write a pending contract.
        parent = json.loads((b.LIT/'potential-lift-certificate-v1/contract.json').read_text())
        evidence = json.loads((b.LIT/'potential-lift-certificate-v1/evidence/results.json').read_text())
        c = copy.deepcopy(parent)
        c['parent50_contract'] = {'sha256': b.sha(b.LIT/'potential-lift-certificate-v1/contract.json')}
        c['parent50_arms'] = {a['cohort']: a for a in evidence['arms']}
        with patch.object(b, 'checked_bytes', side_effect=AssertionError('private open')) as opened:
            b.accepted_parent50(c, parent, evidence)
            for kind in ('incomplete', 'false_zero', 'curve', 'pool', 'potential_path', 'digest'):
                wrong = copy.deepcopy(evidence); changed = copy.deepcopy(c)
                if kind == 'incomplete': wrong['complete'] = False
                if kind == 'false_zero': wrong['arms'][0]['rows'][0]['k'] = False
                if kind == 'curve': wrong['arms'][0]['rows'][1]['charge'] += 1
                if kind == 'pool': changed['private_files'][changed['cohorts']['R']['pool']] = '0'*64
                if kind == 'potential_path': wrong['arms'][0]['old_path_terms_sha256'] = '0'*64
                if kind == 'digest': wrong['arms'][0]['checked_proof_sha256'] = 'not-a-hash'
                # Rebind embedded copies too: arithmetic/provenance must fail.
                changed['parent50_arms'] = {a['cohort']: a for a in wrong['arms']}
                with self.assertRaises(AssertionError): b.accepted_parent50(changed, parent, wrong)
            opened.assert_not_called()

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

    def test_worker_postproof_write_failure_removes_success(self):
        inputs, old = supplied(); c = {'old_arms': {'R': old}, 'parent50_arms': {'R': expected50(inputs)}}
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root/'contract.json').write_text(json.dumps(c))
            out = root/'out'; out.mkdir(); original = b.write
            def fail_status(path, value):
                original(path, value)
                if path.name == 'status.json' and value.get('complete') is True:
                    raise OSError('injected post-proof I/O')
            with patch.object(b, 'HERE', root), patch.object(b, 'check_contract'), \
                 patch.object(b, 'load_inputs', return_value=inputs), patch.object(b, 'write', side_effect=fail_status), \
                 patch.object(run.os, 'sched_setaffinity'), patch.object(run.resource, 'setrlimit'):
                with self.assertRaises(OSError): run.arm('R', root, out, time.monotonic()+30)
            self.assertFalse((out/'R/results.json').exists())
            self.assertFalse(json.loads((out/'R/failure.json').read_text())['complete'])

    def test_failure_unlink_deadline_prevents_failure_write(self):
        with tempfile.TemporaryDirectory() as d:
            previous = signal.signal(signal.SIGALRM, run.expired)
            try:
                with patch.object(Path, 'unlink', side_effect=lambda **_: time.sleep(.2)), \
                     patch.object(b, 'write') as write:
                    with self.assertRaises(run.HardDeadline):
                        run.withdraw_worker(Path(d), {'complete': False}, time.monotonic()+.02)
                    write.assert_not_called()
                with patch.object(b, 'write') as write, patch.object(Path, 'unlink') as unlink:
                    with self.assertRaises(run.HardDeadline):
                        run.withdraw_worker(Path(d), {}, time.monotonic()-.01)
                    unlink.assert_not_called(); write.assert_not_called()
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, previous)

    def test_worker_malformed_deadline_fails_before_private_read(self):
        with tempfile.TemporaryDirectory() as d, patch.object(b, 'load_inputs') as loader:
            with self.assertRaises(AssertionError): run.arm('R', Path(d), Path(d), float('nan'))
            loader.assert_not_called()

    def test_actual_worker_paired_output_matches_independent_checker(self):
        import independent
        inputs, old = supplied()
        c = {'old_arms': {cohort: old for cohort in ('R', 'naming')},
             'parent50_arms': {cohort: expected50(inputs) for cohort in ('R', 'naming')}}
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root/'contract.json').write_text(json.dumps(c))
            out = root/'out'; out.mkdir()
            with patch.object(b, 'HERE', root), patch.object(b, 'check_contract'), \
                 patch.object(b, 'load_inputs', side_effect=lambda *args: copy.deepcopy(inputs)), \
                 patch.object(run.os, 'sched_setaffinity'), patch.object(run.resource, 'setrlimit'):
                for cohort in ('R', 'naming'): run.arm(cohort, root, out, time.monotonic()+30)
            expected = independent.check(inputs['texts'],inputs['banned'],inputs['pool'],inputs['q'],
                inputs['seed'],inputs['alphabet'],inputs['denominator'],
                expected_source_hashes=inputs['source_hashes'],expected_old_banned=inputs['banned'],
                expected_old_certificate=inputs['parent_certificate'])
            for cohort in ('R', 'naming'):
                raw = json.loads((out/cohort/'results.json').read_text())
                self.assertEqual(raw['schema'], 'gamma.potential-tightening.arm.v1')
                self.assertIs(raw['complete'], True); self.assertIs(raw['validation_loaded'], False)
                self.assertEqual(raw['full_shape'], inputs['geometry'])
                for key in ('lifted','tightened','new_only_class_counts','new_only_top_entries','digests','reductions','deltas'):
                    self.assertEqual(tighten.digest(raw['proof'][key]),tighten.digest(expected[key]))

    def test_actual_worker_to_independent_report_full_supplied_pipeline(self):
        import independent
        import report
        import test_report
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); fixture=test_report.fixture(root)
            output=root/'actual-production'; output.mkdir()
            with patch.object(b,'HERE',root),patch.object(b,'check_contract'), \
                 patch.object(b,'load_inputs',side_effect=lambda *args:copy.deepcopy(fixture.inputs)), \
                 patch.object(run.os,'sched_setaffinity'),patch.object(run.resource,'setrlimit'):
                for cohort in ('R','naming'):run.arm(cohort,root,output,time.monotonic()+30)
            arms=[json.loads((output/cohort/'results.json').read_text()) for cohort in ('R','naming')]
            elapsed=max(a['seconds'] for a in arms)+1
            report.write(output/'results.json',{'complete':True,'validation_loaded':False,
                'contract_sha256':fixture.contract_hash,'seconds':elapsed,'arms':arms})
            report.write(output/'supervisor.json',{'complete':True,'phase':'production',
                'contract_sha256':fixture.contract_hash,'elapsed':elapsed+.1,
                'cleanup_seconds':.01,'returncodes':[0,0]})
            mocked_binding=types.SimpleNamespace(check_contract=lambda c:None,
                load_inputs=lambda *args:copy.deepcopy(fixture.inputs))
            with patch.object(report,'HERE',root),patch.object(report,'module',side_effect=lambda name,path:
                    mocked_binding if path.name=='binding.py' else independent), \
                 patch.object(report.os,'sched_setaffinity'),patch.object(report.resource,'setrlimit'):
                for cohort in ('R','naming'):report.worker(cohort,root,output,fixture.output,time.monotonic()+30)
                accepted=report.combine(output,fixture.output,fixture.config,elapsed+10,[0,0])
                self.assertIs(accepted['complete'],True);self.assertIs(accepted['predictions']['P1'],True)



if __name__ == '__main__': unittest.main()
