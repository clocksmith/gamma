"""Invented 300-ID reporter fixtures; no corpus loader or production execution."""
import copy
import hashlib
import json
from pathlib import Path
import signal
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import independent
import prototype
import report


def fixture(root):
    texts = {str(pid): 'aaa' if pid != 299 else 'abx' for pid in range(300)}
    banned = set(texts.values())
    alphabet = [chr(i) for i in range(32, 127)]+['\n']
    seed = alphabet+['ab', 'zz']
    shared = ['aa']; extras = ['ab', 'zz']
    pool = sorted(set(alphabet+shared+extras))
    q = [0 for pid, text in sorted(texts.items()) for start in range(len(text))
         for end in range(start+1, len(text)+1) if text[start:end] in pool]
    source_hashes = {pid: hashlib.sha256(text.encode()).hexdigest() for pid, text in texts.items()}
    lift = prototype.Lift(texts, banned, pool, q, seed, alphabet, 1000000,
                          old_source_hashes=source_hashes, old_banned=banned)
    proof = report.shaped(lift.certificate())
    cert = {'denominator': 1000000, 'numerator': proof['old_numerator'],
            'integer_lower_bound': -(-proof['old_numerator']//1000000),
            'relaxed_paths_numerator': sum(proof['path_numerators'].values()),
            'top_capacity_numerator': proof['old_charge'],
            'per_program_path_numerators': [proof['path_numerators'][pid] for pid in sorted(texts)]}
    old = {'pool_entries': len(pool), 'maximum_entry_length': max(map(len, pool)),
           'shared_learned_entries': len(shared), 'seed_extra_entries': len(extras),
           'seed_extras_sha256': hashlib.sha256(json.dumps(extras, ensure_ascii=True).encode()).hexdigest(),
           'occurrences': len(q), 'certificate': cert}
    index = lift.index
    geometry = {'source_characters': len(index.positions), 'full_groups': len(index.groups),
                'full_distinct_entries': index.distinct_allowed_entries,
                'exact_ban_occurrences': sum(len(ends) for rows in index.banned_ends.values() for ends in rows)}
    bindings = {key: 'a'*64 for key in ('source_sha256', 'seed_sha256', 'pool_sha256',
                'q_sha256', 'old_private_results_sha256', 'old_evidence_sha256', 'full_evidence_sha256')}
    bindings.update(source_hashes_sha256=report.digest(source_hashes),
                    bans_sha256=report.digest(sorted(banned)), banned_entries=len(banned))
    inputs = dict(texts=texts, banned=banned, pool=pool, q=q, seed=seed, alphabet=alphabet,
                  denominator=1000000, source_hashes=source_hashes, parent_certificate=cert,
                  geometry=geometry, bindings=bindings)
    config = {'active': True, 'fit_ids': list(range(300)), 'limits': {
        'worker_seconds': 600, 'production_seconds': 1200, 'report_seconds': 1200,
        'cleanup_seconds': 10, 'address_space_bytes': 8*1024**3,
        'arm_cores': {'R': [6], 'naming': [7]}},
        'old_arms': {cohort: copy.deepcopy(old) for cohort in report.COHORTS},
        'source_hashes': {cohort: source_hashes for cohort in report.COHORTS}}
    report.write(root/'contract.json', config)
    ch = report.sha(root/'contract.json')
    arms = [{'schema': 'gamma.potential-lift.arm.v1', 'complete': True, 'validation_loaded': False,
             'cohort': cohort, 'contract_sha256': ch, 'bindings': bindings,
             'full_shape': geometry, 'proof': copy.deepcopy(proof), 'seconds': .1,
             'peak_rss_kib': 1024, 'phase_seconds': {'input': .01, 'proof': .02}}
            for cohort in report.COHORTS]
    run, output = root/'run', root/'report'
    run.mkdir(); output.mkdir()
    for arm in arms:
        (run/arm['cohort']).mkdir()
        report.write(run/arm['cohort']/'results.json', arm)
    production = {'complete': True, 'validation_loaded': False, 'contract_sha256': ch,
                  'seconds': .2, 'arms': arms}
    supervisor = {'complete': True, 'phase': 'production', 'contract_sha256': ch,
                  'elapsed': .3, 'cleanup_seconds': .01, 'returncodes': [0, 0]}
    report.write(run/'results.json', production); report.write(run/'supervisor.json', supervisor)
    return SimpleNamespace(inputs=inputs, config=config, run=run, output=output,
                           production=production, supervisor=supervisor, contract_hash=ch)


class ReporterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.f = fixture(self.root)
        self.here = patch.object(report, 'HERE', self.root); self.here.start()
        self.load_calls = []
        self.binding = SimpleNamespace(check_contract=lambda c: None, load_inputs=self.load)
        self.modules = patch.object(report, 'module', side_effect=lambda name, path:
                                    self.binding if path.name == 'binding.py' else independent)
        self.modules.start()
        self.resources = patch.object(report.resource, 'setrlimit'); self.resources.start()
        self.affinity = patch.object(report.os, 'sched_setaffinity'); self.affinity.start()

    def tearDown(self):
        self.affinity.stop(); self.resources.stop(); self.modules.stop(); self.here.stop()
        self.temporary.cleanup()

    def load(self, config, work, cohort, deadline):
        self.load_calls.append(cohort)
        self.assertGreater(deadline, time.monotonic())
        return copy.deepcopy(self.f.inputs)

    def worker(self, cohort='R'):
        return report.worker(cohort, self.root/'no-private-files', self.f.run,
                             self.f.output, time.monotonic()+1200)

    def save_production(self):
        report.write(self.f.run/'results.json', self.f.production)
        report.write(self.f.run/'supervisor.json', self.f.supervisor)
        for arm in self.f.production['arms']:
            report.write(self.f.run/arm['cohort']/'results.json', arm)

    def test_complete_fresh_pipeline_and_public_sanitization(self):
        for cohort in report.COHORTS:
            arm = self.worker(cohort)
            self.assertEqual(len(arm['rows']), 257)
            self.assertNotIn('top_entries', arm)
            self.assertNotIn('path_numerators', arm)
            self.assertEqual(set(arm), report.ARM_FIELDS)
        result = report.combine(self.f.run, self.f.output, self.f.config, 10., [0, 0])
        report.publish(self.f.output, result)
        self.assertTrue(report.read(self.f.output/'results.json')['complete'])
        self.assertEqual(self.load_calls, ['R', 'naming'])
        serialized = json.dumps(result)
        for forbidden in ('"texts"', '"q"', '"pool"', '"top_entries"', '"path_numerators"', '"aaa"', '"abx"'):
            self.assertNotIn(forbidden, serialized)
        self.assertFalse(result['m1_claim'])
        self.assertFalse(result['packet_or_witness_claim'])
        self.assertTrue(result['predictions']['P1'])
        self.assertEqual(result['predictions']['P2'], any(row['integer_lower_bound'] > 0
                         for a in result['arms'] for row in a['rows'][1:]))
        self.assertEqual(result['predictions']['P3'], any(a['rows'][256]['integer_lower_bound'] > 0
                         for a in result['arms']))
        self.assertEqual(result['qualification']['fresh_jobs'], 0)
        self.assertIn('exit137', result['qualification']['inherited_failure'])
        for a in result['arms']:
            self.assertEqual(a['largest_positive_k'], max((r['k'] for r in a['rows']
                             if r['integer_lower_bound'] > 0), default=None))
        # Every copied numeric term, memory/time and fixed public schema is checked again.
        saved = report.read(self.f.output/'R.json')
        corruptions = [('old_charge', False), ('old_numerator', saved['old_numerator']+1),
                       ('report_worker_seconds', float('inf')), ('report_peak_rss_kib', 0),
                       ('source_identity_sha256', '0'*64), ('old_pool_entries', 10000000),
                       ('shared_dependencies', 'private source text'), ('source_text', 'DO NOT PUBLISH')]
        for key, value in corruptions:
            changed = copy.deepcopy(saved); changed[key] = value
            if type(value) is float and not report.math.isfinite(value):
                (self.f.output/'R.json').write_text(json.dumps(changed))
            else:
                report.write(self.f.output/'R.json', changed)
            with self.assertRaises((AssertionError, ValueError)):
                report.combine(self.f.run, self.f.output, self.f.config, 10., [0, 0])
        report.write(self.f.output/'R.json', saved)
        for codes in ([False, 0], [0], [0, 1]):
            with self.assertRaises(AssertionError):
                report.combine(self.f.run, self.f.output, self.f.config, 10., codes)
        (self.f.output/'failure.json').write_text('{}')
        with self.assertRaises(AssertionError):
            report.combine(self.f.run, self.f.output, self.f.config, 10., [0, 0])

    def test_failed_or_malformed_production_precedes_private_loading(self):
        base_p, base_s = copy.deepcopy(self.f.production), copy.deepcopy(self.f.supervisor)
        mutations = [lambda p, s: p.update(complete=False), lambda p, s: s.update(complete=False),
                     lambda p, s: s.update(returncodes=[False, 0]),
                     lambda p, s: p['arms'][0]['proof']['rows'].pop(),
                     lambda p, s: p['arms'][0]['proof'].update(old_charge=False),
                     lambda p, s: p['arms'][0]['proof']['class_counts'].update({'1': True}),
                     lambda p, s: p['arms'][0]['proof']['path_numerators'].update({'0': True})]
        for mutation in mutations:
            self.f.production, self.f.supervisor = copy.deepcopy(base_p), copy.deepcopy(base_s)
            mutation(self.f.production, self.f.supervisor); self.save_production()
            with self.assertRaises(AssertionError): self.worker()
            self.assertEqual(self.load_calls, [])
            (self.f.output/'R-failure.json').unlink(missing_ok=True)
        self.f.production, self.f.supervisor = base_p, base_s; self.save_production()
        (self.f.run/'failure.json').write_text('{}')
        with self.assertRaises(AssertionError): self.worker()
        self.assertEqual(self.load_calls, [])

    def test_numeric_proof_and_full_geometry_corruption_rejected_by_fresh_checker(self):
        raw = self.f.production['arms'][0]
        mutations = [lambda r: r['proof']['top_entries']['1'][-1].__setitem__(1, 999999),
                     lambda r: r['full_shape'].update(full_groups=r['full_shape']['full_groups']+1),
                     lambda r: r['proof']['rows'][256].update(one_owner_slots=3),
                     lambda r: r['proof'].update(occurrence_sha256='0'*64)]
        for mutation in mutations:
            damaged = copy.deepcopy(raw); mutation(damaged)
            with self.assertRaises(AssertionError):
                report.replay('R', self.f.inputs, damaged, independent, self.f.config['old_arms']['R'])
        old = copy.deepcopy(self.f.config['old_arms']['R']); old['seed_extra_entries'] += 1
        with self.assertRaises(AssertionError):
            report.replay('R', self.f.inputs, raw, independent, old)
        inputs = copy.deepcopy(self.f.inputs)
        inputs['parent_certificate']['per_program_path_numerators'][0] += 1
        with self.assertRaises(AssertionError):
            report.replay('R', inputs, raw, independent, self.f.config['old_arms']['R'])

    def test_primitive_singleton_body_ban_cannot_be_ignored(self):
        inputs = copy.deepcopy(self.f.inputs)
        inputs['banned'].add('a')
        # Matching the claimed ban/geometry hashes cannot make an old char legal.
        index = independent.full.Index(inputs['texts'], inputs['banned'])
        inputs['geometry'] = {'source_characters': len(index.positions), 'full_groups': len(index.groups),
            'full_distinct_entries': index.distinct_allowed_entries,
            'exact_ban_occurrences': sum(len(ends) for rows in index.banned_ends.values() for ends in rows)}
        raw = copy.deepcopy(self.f.production['arms'][0]); raw['full_shape'] = inputs['geometry']
        with self.assertRaises((AssertionError, ValueError)):
            report.replay('R', inputs, raw, independent, self.f.config['old_arms']['R'])

    def test_setup_and_postwrite_deadlines_fail_without_success(self):
        def setup(c):
            self.assertGreater(signal.getitimer(signal.ITIMER_REAL)[0], 0)
            raise report.HardDeadline('setup')
        self.binding.check_contract = setup
        with self.assertRaises(report.HardDeadline): self.worker()
        self.assertEqual(self.load_calls, [])
        self.assertFalse((self.f.output/'R.json').exists())
        self.assertFalse(report.read(self.f.output/'R-failure.json')['complete'])
        self.binding.check_contract = lambda c: None
        original = report.write
        def after_write(path, value):
            original(path, value)
            if Path(path).name == 'R.json': raise report.HardDeadline('after write')
        with patch.object(report, 'write', side_effect=after_write):
            with self.assertRaises(report.HardDeadline): self.worker()
        self.assertFalse((self.f.output/'R.json').exists())

    def test_publication_failure_after_prose_and_serialization_withdraws_success(self):
        for cohort in report.COHORTS: self.worker(cohort)
        result = report.combine(self.f.run, self.f.output, self.f.config, 10., [0, 0])
        report.publish(self.f.output, result)
        replace = Path.replace
        def after_prose(path, target):
            value = replace(path, target)
            if path.name == 'REPORT.md.pending': raise report.HardDeadline('after prose')
            return value
        previous = signal.signal(signal.SIGALRM, report._expired)
        try:
            signal.setitimer(signal.ITIMER_REAL, 1)
            with patch.object(Path, 'replace', after_prose):
                with self.assertRaises(report.HardDeadline): report.publish(self.f.output, result)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)
        self.assertFalse((self.f.output/'results.json').exists())
        self.assertFalse((self.f.output/'REPORT.md').exists())
        report.withdraw(self.f.output, report.HardDeadline('supervisor failure phase'))
        self.assertFalse(report.read(self.f.output/'results.json')['complete'])
        self.assertIn('no verdict', (self.f.output/'REPORT.md').read_text())
        report.publish(self.f.output, result)
        dumps = json.dumps
        def broken(value, *args, **kwargs):
            if type(value) is dict and value.get('complete') is True: raise OSError('serialization')
            return dumps(value, *args, **kwargs)
        with patch.object(report.json, 'dumps', side_effect=broken):
            with self.assertRaises(OSError): report.publish(self.f.output, result)
        self.assertFalse((self.f.output/'results.json').exists())
        report.withdraw(self.f.output, OSError('supervisor failure phase'))
        self.assertFalse(report.read(self.f.output/'results.json')['complete'])

    def test_worker_failure_unlink_deadline_prevents_failure_write(self):
        target = self.f.output/'R.json'
        previous = signal.signal(signal.SIGALRM, report._expired)
        try:
            with patch.object(Path, 'unlink', side_effect=lambda **_: time.sleep(.2)), \
                 patch.object(report, 'write') as write:
                with self.assertRaises(report.HardDeadline):
                    report.withdraw_worker(target, {'complete': False}, time.monotonic()+.02)
                write.assert_not_called()
            with patch.object(report, 'write') as write, patch.object(Path, 'unlink') as unlink:
                with self.assertRaises(report.HardDeadline):
                    report.withdraw_worker(target, {}, time.monotonic()-.01)
                unlink.assert_not_called(); write.assert_not_called()
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)

    def test_expired_owner_alarm_skips_unguarded_local_unlink(self):
        class OwnerDeadline(BaseException): pass
        (self.f.output/'results.json').write_text('{"complete": true}')
        (self.f.output/'REPORT.md').write_text('stale success')
        def expired(*_): raise OwnerDeadline('one-shot owner deadline')
        previous = signal.signal(signal.SIGALRM, expired)
        try:
            with patch.object(report, 'markdown', side_effect=lambda _: time.sleep(.2)), \
                 patch.object(Path, 'unlink') as unlink:
                signal.setitimer(signal.ITIMER_REAL, .02)
                with self.assertRaises(OwnerDeadline):
                    report.publish(self.f.output, {'complete': True})
                self.assertEqual(signal.getitimer(signal.ITIMER_REAL)[0], 0)
                unlink.assert_not_called()
            # The owner, not publish(), now establishes the failure-I/O guard.
            signal.setitimer(signal.ITIMER_REAL, .5)
            report.withdraw(self.f.output, OwnerDeadline('supervisor failure phase'))
            self.assertFalse(report.read(self.f.output/'results.json')['complete'])
            self.assertIn('no verdict', (self.f.output/'REPORT.md').read_text())
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)

    def test_foreign_hard_deadline_during_failure_write_stops_later_io(self):
        class OwnerDeadline(BaseException): pass
        (self.f.output/'results.json').write_text('{"complete": true}')
        (self.f.output/'REPORT.md').write_text('stale success')
        original = Path.write_text; writes = []
        def slow(path, text, *args, **kwargs):
            writes.append(path.name)
            if path.name == 'REPORT.md.failure': time.sleep(.2)
            return original(path, text, *args, **kwargs)
        def expired(*_): raise OwnerDeadline('owner absolute failure deadline')
        previous = signal.signal(signal.SIGALRM, expired)
        try:
            with patch.object(Path, 'write_text', slow):
                signal.setitimer(signal.ITIMER_REAL, .02)
                with self.assertRaises(OwnerDeadline):
                    report.withdraw(self.f.output, RuntimeError('trigger'))
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)
        self.assertEqual(writes, ['REPORT.md.failure'])
        self.assertFalse((self.f.output/'results.json').exists())
        self.assertFalse((self.f.output/'REPORT.md').exists())

    def test_duplicate_json_keys_and_bool_integer_proof_rejected(self):
        target = self.root/'duplicate.json'; target.write_text('{"complete":false,"complete":true}')
        with self.assertRaises(AssertionError): report.read(target)
        with self.assertRaises(AssertionError): report.exact(False, 0)
        with self.assertRaises(AssertionError): report.exact([True], [1])


if __name__ == '__main__':
    unittest.main()
