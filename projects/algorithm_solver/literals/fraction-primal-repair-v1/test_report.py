"""Invented complete/failure artifacts, source/hash corruption and metadata checks."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import backend
import model
import pool
report = backend.module('fraction_primal_synthetic_report', backend.HERE / 'report.py')


class ReportTests(unittest.TestCase):
    def fixture(self, root):
        here, lit, work, out = [root / name for name in ('here', 'lit', 'work', 'out')]
        for p in (here, lit, work, out):
            p.mkdir()
        texts = {str(i): 'function solve(){return 1}' for i in range(300)}
        seed = sorted(set(next(iter(texts.values())))); bans = backend.dual.sel.forbidden_strings(texts)
        index = pool.implicit.Index(texts, bans)
        q = {p: [[0] * len(pool.implicit.BINS) for _ in t] for p, t in texts.items()}
        cert = index.certificate(q, 256, 1000)
        c = {'ready_to_freeze': True, 'fit_ids': list(range(300)), 'cohorts': {p: p for p in ('R', 'naming')},
             'parent_evidence': 'parent.json', 'parent_private_results': 'parent-private.json', 'parent_q': {}, 'parent_seed': {},
             'private_files': {}, 'code_hashes': {}, 'runtime_files': {},
             'pool': {'capacity': 256, 'denominator': 1000, 'entries': 2048},
             'construction': {'max_arcs': 1_000_000, 'max_transitions': 20_000_000, 'max_pool_characters': 2_000_000},
             'search': {'seconds': 0}, 'solve_order': {'R': ['warm', 'cold'], 'naming': ['cold', 'warm']},
             'limits': {'cohort_seconds': 2400, 'overall_seconds': 2500},
             'decoder_source_files': {}, 'offline_encoder_bytes': 1, 'offline_encoder_scope': 'synthetic'}
        for rel in ('literals.py', 'pass2/working/bitpack.py'):
            path = lit / rel; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((backend.LIT / rel).read_bytes())
            c['decoder_source_files'][rel] = {'sha256': backend.sha(path), 'bytes': path.stat().st_size}
        c['decoder_dependency_bytes'] = sum(v['bytes'] for v in c['decoder_source_files'].values())
        parent_public = {'complete': True, 'validation_loaded': False, 'arms': []}
        parent_private = {'complete': True, 'validation_loaded': False, 'arms': []}
        qualification = {'arms': []}
        prepared = {}
        for cohort in ('R', 'naming'):
            inputs = work / cohort; inputs.mkdir()
            backend.write(inputs / 'fit-sources.json', texts); backend.write(inputs / 'q.json', q)
            backend.write(inputs / 'seed.json', seed)
            c['parent_q'][cohort] = f'{cohort}/q.json'; c['parent_seed'][cohort] = f'{cohort}/seed.json'
            for name in ('fit-sources.json', 'q.json', 'seed.json'):
                c['private_files'][f'{cohort}/{name}'] = backend.sha(inputs / name)
            clean_cert = {k: cert[k] for k in backend.CERT_KEYS}; clean_cert['q_sha256'] = backend.sha(inputs / 'q.json')
            parent_witness = {'dictionary_sha256': backend.sha(inputs / 'seed.json'), 'objective': model.exact(texts, seed)['F']}
            parent_public['arms'].append({'cohort': cohort, 'fit_source_sha256': backend.sha(inputs / 'fit-sources.json'),
                                         'certificate': clean_cert, 'witnesses': {'seed': parent_witness}})
            parent_private['arms'].append({'cohort': cohort, 'complete': True, 'validation_loaded': False,
                    'fit_source_sha256': backend.sha(inputs / 'fit-sources.json'), 'optimization': {'certificate': clean_cert},
                    'witnesses': {'seed': parent_witness}})
            qualification['arms'].append({'arm': 'control' if cohort == 'R' else 'scope_joint', 'width': 8,
                'qualification': {p: {'passed': True} for p in texts},
                'per_problem': {p: {'source_sha256': backend.analyze.sha(t.encode())} for p, t in texts.items()}})
            folder = out / cohort; folder.mkdir()
            words, info = pool.build(index, q, seed, 1000, 256, 2048)
            backend.write(folder / 'pool.json', words); backend.write(folder / 'pool-provenance.json', info)
            m = model.build(texts, words, 256, seed, bans, **c['construction'])
            witnesses = {'seed': backend.measure(texts, seed, folder / 'seed', c['decoder_dependency_bytes'])}; solvers = {}
            for name in c['solve_order'][cohort]:
                vocab, receipt, _ = model.solve(m, texts, words, name == 'warm', 0, bans)
                if receipt['feasible']:
                    witnesses[name] = backend.measure(texts, vocab, folder / name, c['decoder_dependency_bytes'])
                solvers[name] = receipt
            prepared[cohort] = {'cohort': cohort, 'complete': True, 'validation_loaded': False, 'fit_problems': 300,
                'fit_source_sha256': backend.sha(inputs / 'fit-sources.json'), 'parent_q_sha256': clean_cert['q_sha256'],
                'parent_full_class_certificate': {k: cert[k] for k in backend.CERT_KEYS},
                'pool_sha256': backend.sha(folder / 'pool.json'), 'pool_provenance_sha256': backend.sha(folder / 'pool-provenance.json'),
                'pool_counts': {k: v for k, v in info.items() if k != 'provenance'}, 'model_sha256': model.fingerprint(m),
                'arcs': m['arcs'], 'variables': m['variables'], 'transitions': m['transitions'], 'build_seconds': m['build_seconds'],
                'solve_order': c['solve_order'][cohort], 'solvers': solvers, 'witnesses': witnesses, 'seconds': 30}
            backend.write(folder / 'status.json', {'phase': 'complete', 'complete': True})
        backend.write(work / 'parent-private.json', parent_private)
        parent_public['private_results_sha256'] = backend.sha(work / 'parent-private.json')
        c['private_files']['parent-private.json'] = parent_public['private_results_sha256']
        backend.write(lit / 'parent.json', parent_public)
        proof = lit / 'binding-descent-v1/evidence/results.json'; proof.parent.mkdir(parents=True)
        backend.write(proof, qualification)
        for rel in ('parent.json', 'binding-descent-v1/evidence/results.json'):
            c['code_hashes'][rel] = backend.sha(lit / rel)
        backend.write(here / 'contract.json', c); chash = backend.sha(here / 'contract.json')
        for cohort, raw in prepared.items():
            raw['contract_sha256'] = chash; backend.write(out / cohort / 'results.json', raw)
        aggregate = {'complete': True, 'validation_loaded': False, 'contract_sha256': chash,
                     'arms': list(prepared.values()), 'seconds': 60}
        backend.write(out / 'results.json', aggregate)
        return here, lit, work, out, aggregate

    def test_complete_corruption_and_failure_dominance(self):
        with tempfile.TemporaryDirectory() as temp:
            here, lit, work, out, original = self.fixture(Path(temp))
            with patch.object(backend, 'LIT', lit):
                build = lambda: report.build_report(out, work, here, lit)
                clean = build(); self.assertTrue(clean['complete']); self.assertTrue(clean['predictions']['P1'])
                self.assertGreaterEqual(clean['decoded_packets'], 1200)
                encoded = json.dumps(clean)
                self.assertNotIn('function solve', encoded); self.assertNotIn('provenance', encoded)
                report.write_report(clean, here)
                def corrupt(fn):
                    raw = copy.deepcopy(original); fn(raw)
                    backend.write(out / 'results.json', raw)
                    for arm in raw['arms']:
                        backend.write(out / arm['cohort'] / 'results.json', arm)
                    with self.assertRaises((AssertionError, ValueError)):
                        build()
                    backend.write(out / 'results.json', original)
                    for arm in original['arms']:
                        backend.write(out / arm['cohort'] / 'results.json', arm)
                corrupt(lambda r: r.__setitem__('seconds', 2501))
                corrupt(lambda r: r['arms'][0].__setitem__('seconds', 61))
                corrupt(lambda r: r['arms'][0].__setitem__('model_sha256', '0' * 64))
                corrupt(lambda r: r['arms'][0]['solvers']['warm'].__setitem__('model_sha256', '0' * 64))
                corrupt(lambda r: r['arms'][0]['parent_full_class_certificate'].__setitem__('integer_lower_bound', 9999))
                corrupt(lambda r: r['arms'][0]['witnesses']['warm'].__setitem__('characters', 0))
                corrupt(lambda r: r['arms'][0]['solvers']['warm'].__setitem__('objective', -999999))
                corrupt(lambda r: r['arms'][0]['solvers']['warm'].__setitem__('solver_run_seconds', 999999))
                corrupt(lambda r: r['arms'][0]['solvers']['warm'].__setitem__('optimal', not r['arms'][0]['solvers']['warm']['optimal']))
                corrupt(lambda r: r['arms'][0].__setitem__('build_seconds', 30))
                packet = out / 'R/warm/packets/0.bin'; data = packet.read_bytes()
                packet.write_bytes(data[:-1] + bytes([255]))
                with self.assertRaises(AssertionError):build()
                packet.write_bytes(data)
                source = work / 'R/fit-sources.json'; data = source.read_bytes(); source.write_bytes(data + b' ')
                with self.assertRaises(AssertionError):build()
                source.write_bytes(data)
                # Publication failure must remove the previous successful prose.
                bad = copy.deepcopy(original); bad['seconds'] = 999999
                backend.write(out / 'results.json', bad)
                with self.assertRaises(AssertionError):
                    report.publish(out, work, here, lit)
                stale_replacement = json.loads((here / 'evidence/results.json').read_text())
                self.assertFalse(stale_replacement['complete']); self.assertIsNone(stale_replacement['verdicts'])
                self.assertIn('no verdict', (here / 'README.md').read_text())
                self.assertNotIn('| Cohort |', (here / 'README.md').read_text())
                backend.write(out / 'results.json', original)
                failure = {'complete': False, 'validation_loaded': False, 'partial_witnesses_promoted': False,
                           'contract_sha256': original['contract_sha256'], 'exception': 'TimeoutError', 'seconds': 2500}
                backend.write(out / 'failure.json', failure)
                # Failure dominates stale complete results and avoids all private-input reads.
                source.unlink(); failed = build(); self.assertFalse(failed['complete'])
                self.assertEqual(failed['failure_type'], 'TimeoutError')
                failure['validation_loaded'] = True; backend.write(out / 'failure.json', failure)
                with self.assertRaises(AssertionError):build()


if __name__ == '__main__':
    unittest.main()
