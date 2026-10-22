"""Synthetic encoding-only controls; no corpus reads or candidate execution."""
from pathlib import Path
import copy
import importlib.util
import json
import os
import resource
import sys
import unittest
import tempfile
sys.dont_write_bytecode = True
if hasattr(os, "sched_getaffinity"):
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
if sys.platform == 'darwin':
    # macOS refuses an address-space cap below the interpreter's existing mappings.
    print('test_incumbent: 256 MiB RLIMIT_AS NOT ENFORCED on macOS; '
          'memory-limit evidence requires Linux', file=sys.stderr)
else:
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024,) * 2)
resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('incumbent_under_test', HERE / 'incumbent.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class IncumbentTests(unittest.TestCase):
    def test_portable_optimizer_integration(self):
        optimizer = m.module('portable_optimizer', HERE / 'optimizer.py')
        state, _ = self.validate()
        retained, _, detail, _ = m.search_with_incumbent(
            self.sources, self.pool, 7, state, optimizer.optimize,
            lambda: False, max_rounds=2, max_trials=16)
        self.assertLessEqual(m.core.cost(retained), m.core.cost(state))
        self.assertEqual(retained['coverage'], 2)
        self.assertLessEqual(detail['trials'], 16)

    def setUp(self):
        self.sources = {'1': {'base': 'abab', 'alt': 'baba'}, '2': {'base': 'bbaa', 'alt': 'aabb'}}
        self.pool = ['a', 'b', 'ab', 'bb', 'aa']
        self.fixed = {'1': 'base', '2': 'base'}
        self.expected = dict(language='javascript', width=7, cohort_sha256='c' * 64,
            pool_sha256='d' * 64, problem_ids=['1', '2'], objective=m.OBJECTIVE.copy())
        self.descriptor = copy.deepcopy(self.expected)
        self.strings = ['a', 'ab', 'b']
        self.dictionary = m.table_bytes(self.strings)
        fixed = {pid: {'base': vs['base']} for pid, vs in self.sources.items()}
        state = m.core.evaluate(fixed, self.strings, 7, mandatory=())
        self.manifest = {k: state[k] for k in ['coverage', 'denominator', 'uncovered', 'selections', 'dictionary_bytes', 'packet_bytes', 'package_bytes']}
        self.manifest.update(language='javascript', width=7, policy='compression', arm='dictionary-only',
            entries=3, dictionary_sha256=m.sha(self.dictionary), whole_program_entries=0,
            implicit_helpers_imports_wrappers_or_operands=0, programs=[])
        self.packets = {}
        for pid, vs in fixed.items():
            source = vs['base'].encode();parts = state['parsed'][(pid, 'base')]
            ids = [self.strings.index(p) for p in parts];packet = m.codec.packet(ids, 7, self.dictionary)
            self.packets[pid] = packet
            self.manifest['programs'].append(dict(problem_id=pid, variant='base', represented=True,
                source_sha256=m.sha(source), source_bytes=len(source), sequence=ids, selections=len(ids),
                selection_bits=7 * len(ids), framing_bits=328, padding_bits=(-7 * len(ids)) % 8,
                packet_bytes=len(packet), packet_sha256=m.sha(packet)))

    def validate(self):
        return m.validate_payload(self.descriptor, self.expected, self.manifest, self.dictionary,
                                  self.packets, self.sources, self.pool, self.fixed)

    def test_valid_import_resegments_every_variant(self):
        state, receipt = self.validate()
        self.assertEqual(state['coverage'], 2)
        self.assertEqual(len(state['parsed']), 4)
        self.assertEqual(receipt['additional_backward_variant_parses'], 6)
        self.assertEqual(receipt['additional_forward_variant_checks'], 6)

    def test_wrong_identity_fields(self):
        for field in ['language', 'width', 'cohort_sha256', 'pool_sha256', 'problem_ids', 'objective']:
            with self.subTest(field=field):
                self.descriptor = copy.deepcopy(self.expected);self.descriptor[field] = None
                with self.assertRaises(ValueError):self.validate()

    def test_both_sides_wrong_objective(self):
        self.expected['objective'] = self.descriptor['objective'] = ['minimize_bits']
        with self.assertRaises(ValueError):self.validate()

    def test_manifest_width_mismatch(self):
        self.manifest['width'] = 8
        with self.assertRaises(ValueError):self.validate()

    def test_incomplete_coverage(self):
        self.manifest['programs'][0]['represented'] = False
        with self.assertRaises(ValueError):self.validate()

    def test_missing_or_duplicate_problem(self):
        self.manifest['programs'][1] = self.manifest['programs'][0]
        with self.assertRaises(ValueError):self.validate()

    def test_unqualified_variant(self):
        self.manifest['programs'][0]['variant'] = 'invented'
        with self.assertRaises(ValueError):self.validate()

    def test_changed_source_bytes(self):
        self.sources['1']['base'] = 'abba'
        with self.assertRaises(ValueError):self.validate()

    def test_unbound_packet(self):
        self.packets['1'] = self.packets['1'][:-1] + b'\xff'
        with self.assertRaises((AssertionError, ValueError)):self.validate()

    def test_sequence_metric_disagrees(self):
        self.manifest['programs'][0]['sequence'] = [0]
        with self.assertRaises(ValueError):self.validate()

    def test_false_total_cost(self):
        self.manifest['selections'] -= 1
        with self.assertRaises(ValueError):self.validate()

    def test_candidate_pool_rejects_outsider(self):
        self.pool.remove('ab')
        with self.assertRaises(ValueError):self.validate()

    def test_whole_program_entry(self):
        with self.assertRaises(ValueError):m.validate_table(['abab'], self.sources, ['abab'], 7)

    def test_cap_and_duplicate_checks(self):
        with self.assertRaises(ValueError):m.validate_table(['x' + str(i) for i in range(129)], self.sources, ['x' + str(i) for i in range(129)], 7)
        with self.assertRaises(ValueError):m.validate_table(['a', 'a'], self.sources, self.pool, 7)

    def bound_files(self, root):
        def save(name, data):
            path = root / name;path.write_bytes(data)
            return {'path': str(path), 'sha256': m.sha(data)}
        self.manifest['label'] = 'synthetic-fixed'
        descriptor = copy.deepcopy(self.descriptor)
        descriptor.update(label='synthetic-fixed',
            manifest=save('manifest.json', json.dumps(self.manifest).encode()),
            dictionary=save('dictionary.ltd', self.dictionary),
            packets={pid:save(pid + '.ltv', data) for pid,data in self.packets.items()})
        audit = {'status':'passed','results':[{'label':'synthetic-fixed',**{k:self.manifest[k] for k in ['coverage','denominator','selections','package_bytes','entries']}}]}
        descriptor['audit'] = save('audit.json', json.dumps(audit).encode())
        return descriptor, audit

    def test_loader_checks_audit_status_and_membership(self):
        with tempfile.TemporaryDirectory() as temp:
            descriptor, audit = self.bound_files(Path(temp))
            state,_ = m.load_incumbent(descriptor,self.expected,self.sources,self.pool,self.fixed)
            self.assertEqual(state['coverage'],2)
            for changed in [{'status':'failed','results':audit['results']},{'status':'passed','results':[]}]:
                raw=json.dumps(changed).encode();Path(descriptor['audit']['path']).write_bytes(raw)
                descriptor['audit']['sha256']=m.sha(raw)
                with self.assertRaises(ValueError):m.load_incumbent(descriptor,self.expected,self.sources,self.pool,self.fixed)

    def test_loader_rejects_changed_pinned_file(self):
        with tempfile.TemporaryDirectory() as temp:
            descriptor,_ = self.bound_files(Path(temp))
            Path(descriptor['dictionary']['path']).write_bytes(b'changed')
            with self.assertRaises(ValueError):m.load_incumbent(descriptor,self.expected,self.sources,self.pool,self.fixed)

    def test_worse_valid_state_cannot_replace_incumbent(self):
        initial, _ = self.validate();best = m.MonotonicBest(self.sources, self.pool, 7, initial)
        worse = m.core.evaluate(self.sources, ['a', 'b'], 7, mandatory=())
        best.consider(worse, 'worse')
        self.assertEqual(m.core.cost(best.best), m.core.cost(initial))
        self.assertFalse(best.history[-1]['accepted'])

    def test_coverage_loss_cannot_replace_incumbent(self):
        initial, _ = self.validate();best = m.MonotonicBest(self.sources, self.pool, 7, initial)
        best.consider(m.core.evaluate(self.sources, ['a'], 7, mandatory=()), 'unreachable')
        self.assertEqual(best.best['coverage'], 2)

    def test_forged_state_is_rejected(self):
        initial, _ = self.validate();best = m.MonotonicBest(self.sources, self.pool, 7, initial)
        bad = copy.deepcopy(initial);bad['selections'] = 0
        with self.assertRaises(ValueError):best.consider(bad, 'bad')

    def test_intermediate_best_survives_worse_final_trajectory(self):
        initial, _ = self.validate()
        better = m.core.evaluate(self.sources, self.pool, 7, mandatory=())
        worse = m.core.evaluate(self.sources, ['a', 'b'], 7, mandatory=())
        def fake(sources, start, pool, coordinated, width, expired, **kw):
            self.assertIs(start, initial);self.assertEqual(coordinated, {})
            kw['observe'](better, 'round:1');kw['observe'](worse, 'round:2')
            return worse, {'trace': ['preserved-worse-trajectory']}
        retained, trajectory, detail, checks = m.search_with_incumbent(self.sources, self.pool, 7,
            initial, fake, lambda: False, max_rounds=2, max_trials=4)
        self.assertEqual(m.core.cost(retained), m.core.cost(better))
        self.assertEqual(m.core.cost(trajectory), m.core.cost(worse))
        self.assertEqual(detail['trace'], ['preserved-worse-trajectory'])
        self.assertGreater(checks['additional_backward_variant_parses'], 0)
        self.assertTrue(all(tuple(a['retained_cost']) >= tuple(b['retained_cost']) for a,b in zip(checks['history'], checks['history'][1:])))


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(IncumbentTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
               'synthetic_only': True, 'corpus_encodings': 0, 'source_executions': 0}
    print(json.dumps(summary))
    sys.exit(not result.wasSuccessful())
