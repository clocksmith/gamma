import copy
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from algsolve.approved_library import ApprovedLibrary, build, digest
from algsolve.doppler_runtime import sha
from algsolve.doppler_lookup import build_index, DopplerLookup, calibrate_development
from algsolve.judge.judge import Verdict
from test_answer import query
from test_approved_library import fixture


class Encoder:
    identity = {'runtime': 'fixture', 'models': {'embedding': {'manifest': 'frozen'}}}
    last_receipt = {'total_ms': 1}

    def encode(self, texts, **kwargs):
        return np.tile(np.array([1.] + [0.]*1023, dtype=np.float32), (len(texts), 1))


class LookupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.encoder = Encoder()
        self.entry, inventory, results = fixture()
        protected = copy.deepcopy(self.entry)
        protected.key = 'lc:protected'
        protected.slug = 'protected'
        inventory.append({'key': protected.key, 'excluded': 'protected_composition_alias'})
        manifest = build([self.entry], inventory, results, evidence={})
        self.catalog = ApprovedLibrary(manifest)
        self.catalog_path = self.root/'approved.json'
        self.catalog_path.write_text(json.dumps(manifest))
        self.entries = self.root/'input.jsonl'
        self.entries.write_text(''.join(json.dumps(asdict(e))+'\n' for e in [self.entry, protected]))
        self.index = self.root/'index'
        build_index(self.encoder, self.entries, self.catalog_path, self.index)

    def test_protected_entries_excluded_and_completed_build_resumes_without_compute(self):
        with patch.object(self.encoder, 'encode', side_effect=AssertionError('No repeat inference')):
            build_index(self.encoder, self.entries, self.catalog_path, self.index)
        loaded = DopplerLookup(self.encoder, self.index)
        self.assertEqual(list(loaded.index.by_key), [self.entry.key])

    def test_runtime_or_vector_drift_rejected(self):
        other = Encoder()
        other.identity = {'runtime': 'changed', 'models': self.encoder.identity['models']}
        with self.assertRaisesRegex(ValueError, 'encoder'):
            DopplerLookup(other, self.index)
        path = self.index/'vectors.jsonl'
        path.write_text(path.read_text()+' ')
        with self.assertRaisesRegex(ValueError, 'artifact changed'):
            DopplerLookup(self.encoder, self.index)

    def test_cached_reference_requires_catalog_pins_and_never_recomputes_documents(self):
        vectors, keys = self.root/'reference.npy', self.root/'keys.json'
        np.save(vectors, self.encoder.encode(['a', 'b']))
        keys.write_text(json.dumps([self.entry.key, 'lc:protected']))
        body = {k: v for k, v in self.catalog.manifest.items() if k != 'sha256'}
        body['runtime_files_sha256'] = {
            'data/derived/'+name: sha(path) for name, path in (
                ('corpus_entries.jsonl', self.entries), ('corpus_embeddings.npy', vectors),
                ('corpus_embedding_keys.json', keys))}
        self.catalog_path.write_text(json.dumps(dict(body, sha256=digest(body))))
        output = self.root/'reference-index'
        with patch.object(self.encoder, 'encode', side_effect=AssertionError('No document recomputation')):
            build_index(self.encoder, self.entries, self.catalog_path, output,
                        reference_vectors=vectors, reference_keys=keys)
        loaded = DopplerLookup(self.encoder, output)
        self.assertEqual(list(loaded.index.by_key), [self.entry.key])
        keys.write_text('[]')
        with self.assertRaisesRegex(ValueError, 'Reference index differs'):
            build_index(self.encoder, self.entries, self.catalog_path, self.root/'bad',
                        reference_vectors=vectors, reference_keys=keys)

    def test_no_calibration_never_approves_code(self):
        result = DopplerLookup(self.encoder, self.index).recognize(query())
        self.assertIsNone(result['code'])
        self.assertEqual(result['reason'], 'doppler_calibration_required')
        self.assertEqual(result['candidates'][0]['key'], self.entry.key)

    def calibrate(self):
        path = self.root/'dev.json'
        path.write_text(json.dumps({'partition': 'development', 'cases': [
            {'id': 'max', 'kind': 'informal', 'query': 'Return the maximum.',
             'expected': {'action': 'match', 'keys': [self.entry.key]}},
        ]}))
        lookup = DopplerLookup(self.encoder, self.index)
        # Calibration expects a real shortlist; use a second, known-wrong candidate.
        candidates = [{'key': self.entry.key, 'score': 1.}, {'key': 'lc:other', 'score': 0.}]
        with patch.object(lookup, 'rank', return_value=(candidates, {'total_ms': 1.})):
            calibrate_development(lookup, path, self.root/'calibration')
        return self.root/'calibration/calibration.json'

    def test_calibrated_answer_keeps_public_example_and_source_gates(self):
        lookup = DopplerLookup(self.encoder, self.index, catalog=self.catalog, calibration=self.calibrate())
        q = query(3)
        q.statement, q.starter_code = self.entry.statement, self.entry.starter_code
        with patch('algsolve.answer.validate.judge_problem', return_value=Verdict(True, None, 1, 1, 0)) as check:
            result = lookup.recognize(q)
        check.assert_called_once()
        self.assertEqual(result['decision'], 'answered')
        self.assertFalse(result['recognition_qualified'])
        q.public_tests = []
        self.assertEqual(lookup.recognize(q)['reason'], 'query_has_no_public_examples')
        self.entry.references[0]['code'] += '\n# modified'
        lookup.index.entries[0].references[0]['code'] += '\n# modified'
        # Exact specification bypasses fuzzy confidence, so this reaches the
        # source gate even though this fixture intentionally indexes one item.
        changed = query(3)
        changed.statement, changed.starter_code = self.entry.statement, self.entry.starter_code
        self.assertEqual(lookup.recognize(changed)['reason'], 'stored_answer_not_approved')

    def test_calibration_threshold_edits_rejected(self):
        path = self.calibrate()
        calibration = json.loads(path.read_text())
        calibration['thresholds']['min_score'] -= 1
        path.write_text(json.dumps(calibration))
        with self.assertRaisesRegex(ValueError, 'development evidence'):
            DopplerLookup(self.encoder, self.index, calibration=path)


if __name__ == '__main__':
    unittest.main()
