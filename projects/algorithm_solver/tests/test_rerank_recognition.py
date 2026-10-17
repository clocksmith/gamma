import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from algsolve.rerank_recognition import (
    bind_file, calibrate, diagnostic_entries, load_rows, partition_queries,
    rerank_candidates, summarize,
)


def query(qid, target, kind='exact'):
    return {'qid': qid, 'target': target, 'kind': kind, 'group': qid}


def row(qid, target, candidates):
    return {**query(qid, target), 'reranked': candidates, 'retrieved': candidates,
            'retrieval_seconds': .1, 'rerank_seconds': 2., 'validated_keys': ['known']}


class RecognitionTests(unittest.TestCase):
    def test_split_rejects_shared_queries_targets_and_groups(self):
        dev = query('dq0', 'known')
        for evaluation in [query('dq0', 'other'), query('rq0', 'known'),
                           dict(query('rq0', 'other'), group='dq0')]:
            with self.assertRaises(ValueError):
                partition_queries({'recognition_dev': [dev], 'recognition': [evaluation]})

    def test_absent_diagnostic_excludes_alias_and_whole_family_only(self):
        entries = [SimpleNamespace(slug=slug, members=members) for slug, members in
                   [('stock', ['a']), ('stock-ii', ['b']), ('other-alias', ['source']), ('sum', ['d'])]]
        q = dict(query('dq', None, 'absent_exact'), problem_uid='source')
        self.assertEqual(diagnostic_entries(entries, q, {'source': SimpleNamespace(slug='stock', uid='source')}), [3])
        self.assertEqual(diagnostic_entries(entries, query('rq', 'stock'), {}), [0, 1, 2, 3])

    def test_calibration_uses_exact_boundaries_and_requires_complete_dev(self):
        rows = [row('d1', 'known', [{'key': 'known', 'score': .12345678}, {'key': 'x', 'score': 0.}]),
                row('d2', None, [{'key': 'x', 'score': .12345677}, {'key': 'y', 'score': 0.}])]
        expected = [query('d1', 'known'), query('d2', None)]
        thresholds = calibrate(rows, expected)
        self.assertEqual((thresholds['dev_correct'], thresholds['dev_wrong']), (1, 0))
        for invalid in [rows[:1], rows + rows[:1], [dict(rows[0], qid='eval'), rows[1]],
                        [dict(rows[0], target='other'), rows[1]]]:
            with self.assertRaises(ValueError):
                calibrate(invalid, expected)

    def test_wrong_tied_matches_can_only_be_abstained(self):
        candidates = [{'key': 'wrong', 'score': -2.}, {'key': 'known', 'score': -2.}]
        gates = calibrate([row('d1', 'known', candidates)], [query('d1', 'known')])
        self.assertEqual(gates['dev_wrong'], 0)
        self.assertEqual(gates['dev_correct'], 0)

    def test_frozen_artifact_and_resumption_reject_drift(self):
        with TemporaryDirectory() as temp:
            path = Path(temp)/'contract.json'
            bind_file(path, {'version': 1})
            bind_file(path, {'version': 1})
            with self.assertRaises(ValueError):
                bind_file(path, {'version': 2})
            path.write_text(json.dumps(query('d', 'wrong'))+'\n')
            with self.assertRaises(ValueError):
                load_rows(path, [query('d', 'known')])
            path.write_text((json.dumps(query('d', 'known'))+'\n')*2)
            with self.assertRaises(ValueError):
                load_rows(path, [query('d', 'known')])

    def test_reranking_preserves_identity_and_rejects_invalid_scores(self):
        candidates = [{'key': 'a', 'score': 1}, {'key': 'b', 'score': 2}]
        self.assertEqual([c['key'] for c in rerank_candidates(candidates, [3., -1.])], ['a', 'b'])
        for scores in [[1], [1, float('nan')], [True, 1]]:
            with self.assertRaises(ValueError):
                rerank_candidates(candidates, scores)

    def test_summary_separates_coverage_provenance_absence_and_full_latency(self):
        rows = [row('a', 'known', [{'key': 'known', 'score': 2.}, {'key': 'x', 'score': 1.}]),
                dict(row('b', None, [{'key': 'x', 'score': 0.}, {'key': 'y', 'score': -1.}]), kind='absent_exact')]
        gates = {'min_score': 1., 'min_margin': 0.}
        result = summarize(rows, gates, gates)
        self.assertEqual(result['reranked']['by_kind']['exact']['correct_match'], 1)
        self.assertEqual(result['reranked']['by_kind']['exact']['returned_independently_validated'], 1)
        self.assertEqual(result['reranked']['by_kind']['controlled_absent']['correct_abstention'], 1)
        self.assertAlmostEqual(result['baseline']['p50_seconds'], .1)
        self.assertAlmostEqual(result['reranked']['p50_seconds'], 2.1)


if __name__ == '__main__':
    unittest.main()
