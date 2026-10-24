"""Invented adapter, activation and q-shape checks; never private corpus reads."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import time
import types
import unittest
from unittest.mock import patch
import numpy as np
import binding as b
import production
import prototype
import run
import make_contract


def supplied():
    texts = {'0': 'abcd', '1': 'aefg'}; banned = set(texts.values())
    pool = sorted(set(''.join(texts.values())) | {'z'}); q = [0]*8
    index = prototype.full.Index(texts, banned)
    shape = {'source_characters': 8, 'full_groups': len(index.groups),
             'full_distinct_entries': index.distinct_allowed_entries,
             'exact_ban_occurrences': sum(len(s) for rows in index.banned_ends.values() for s in rows)}
    cert = {'denominator': 7, 'per_program_path_numerators': [252, 252],
            'relaxed_paths_numerator': 504, 'top_capacity_numerator': 0,
            'numerator': 504, 'integer_lower_bound': 72}
    return {'texts': texts, 'banned': banned, 'pool': pool, 'q': q, 'seed': pool,
            'alphabet': pool, 'denominator': 7, 'source_hashes': prototype.source_hashes(texts),
            'parent_certificate': cert, 'geometry': shape, 'bindings': {}}, {
            'shared_learned_entries': 0, 'seed_extra_entries': 0, 'occurrences': 8,
            'seed_extras_sha256': hashlib.sha256(b'[]').hexdigest()}


class ExecutionTests(unittest.TestCase):
    def test_adapter_old_parity_and_full_curve(self):
        inputs, old = supplied(); proof, shape = production.execute(inputs, old)
        self.assertEqual(shape, inputs['geometry']); self.assertEqual(len(proof['rows']), 257)
        self.assertEqual(proof['rows'][0]['integer_lower_bound'], 72)
        self.assertLess(proof['rows'][-1]['numerator'], 0)

    def test_adapter_parent_order_geometry_and_extra_corruption(self):
        for key in ('paths', 'charge', 'shape', 'extras'):
            inputs, old = supplied()
            if key == 'paths': inputs['parent_certificate']['per_program_path_numerators'][0] += 1
            if key == 'charge': inputs['parent_certificate']['top_capacity_numerator'] += 1
            if key == 'shape': inputs['geometry']['full_distinct_entries'] += 1
            if key == 'extras': old['seed_extra_entries'] += 1
            with self.assertRaises(AssertionError): production.execute(inputs, old)

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

    def test_public_metadata_checks_without_private_access(self):
        c = make_contract.build()
        self.assertIs(c['active'], False)
        c['active'] = True  # In-memory public-check fixture; no active file written.
        env = {k: '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')}
        with patch.dict(os.environ, env), patch.object(b, 'checked_bytes', side_effect=AssertionError('private open')) as opened:
            b.check_contract(c)
            for kind in ('public_hash', 'source_identity', 'parent_certificate'):
                wrong = copy.deepcopy(c)
                if kind == 'public_hash': wrong['public_files']['all-length-fraction-v1/evidence/results.json'] = '0'*64
                if kind == 'source_identity': wrong['source_hashes']['R'][str(c['fit_ids'][0])] = '0'*64
                if kind == 'parent_certificate': wrong['old_arms']['R']['certificate']['numerator'] += 1
                with self.assertRaises(AssertionError): b.check_contract(wrong)
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
        inputs, old = supplied(); c = {'old_arms': {'R': old}}
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

    def test_worker_malformed_deadline_fails_before_private_read(self):
        with tempfile.TemporaryDirectory() as d, patch.object(b, 'load_inputs') as loader:
            with self.assertRaises(AssertionError): run.arm('R', Path(d), Path(d), float('nan'))
            loader.assert_not_called()

    def test_actual_worker_output_matches_independent_report_schema(self):
        import report
        import independent
        import test_report
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); fixture = test_report.fixture(root)
            rawdir = root/'actual-production'; rawdir.mkdir()
            with patch.object(b, 'HERE', root), patch.object(b, 'check_contract'), \
                 patch.object(b, 'load_inputs', side_effect=lambda *args: copy.deepcopy(fixture.inputs)), \
                 patch.object(run.os, 'sched_setaffinity'), patch.object(run.resource, 'setrlimit'):
                for cohort in ('R', 'naming'): run.arm(cohort, root, rawdir, time.monotonic()+30)
            arms = [json.loads((rawdir/cohort/'results.json').read_text()) for cohort in ('R', 'naming')]
            elapsed = max(a['seconds'] for a in arms)+1
            report.write(rawdir/'results.json', {'complete': True, 'validation_loaded': False,
                'contract_sha256': fixture.contract_hash, 'seconds': elapsed, 'arms': arms})
            report.write(rawdir/'supervisor.json', {'complete': True, 'phase': 'production',
                'contract_sha256': fixture.contract_hash, 'elapsed': elapsed+.1,
                'cleanup_seconds': .01, 'returncodes': [0, 0]})
            binding = types.SimpleNamespace(check_contract=lambda c: None,
                load_inputs=lambda *args: copy.deepcopy(fixture.inputs))
            with patch.object(report, 'HERE', root), patch.object(report, 'module',
                 side_effect=lambda name, path: binding if path.name == 'binding.py' else independent), \
                 patch.object(report.os, 'sched_setaffinity'), patch.object(report.resource, 'setrlimit'):
                for cohort in ('R', 'naming'):
                    report.worker(cohort, root, rawdir, fixture.output, time.monotonic()+30)
                result = report.combine(rawdir, fixture.output, fixture.config, elapsed+10, [0, 0])
                self.assertIs(result['complete'], True)
                self.assertIs(result['predictions']['P1'], True)


if __name__ == '__main__': unittest.main()
