import copy
import unittest

from algsolve import rerank_policy_comparison as p


def case(ident='one', target='right'):
    return {'id': ident, 'query': 'Find the matching contract.', 'target': target,
            'documents': [{'key': 'wrong', 'text': 'Related but different.'},
                          {'key': 'right', 'text': 'The requested contract.'}]}


def observation(c):
    # Raw yes favors the wrong candidate; yes-minus-no favors the correct one.
    return {'id': c['id'], 'case_sha256': p.digest(c), 'evidence': [
        dict(key=d['key'], document=d['text'], trueLogit=yes, falseLogit=no)
        for d, yes, no in zip(c['documents'], (10., 9.), (20., 0.))]}


def cohort(cases):
    return {'schema': 'gamma.rerank-policy-input.v1', 'partition': 'development', 'cases': cases}


class ComparisonTests(unittest.TestCase):
    def test_identical_logits_produce_distinct_ranking_and_calibration(self):
        c = case(); obs = observation(c)
        result = p.summarize(cohort([c]), [obs])
        self.assertEqual(result['top1_disagreements'], 1)
        raw = result['policies']['true_logit']; diff = result['policies']['logit_difference']
        self.assertEqual((raw['top1_correct'], diff['top1_correct']), (0, 1))
        self.assertEqual((raw['correct_accepted'], diff['correct_accepted']), (0, 1))
        self.assertNotEqual(raw['thresholds'], diff['thresholds'])
        self.assertFalse(result['recognition_qualified'])
        self.assertEqual(obs, observation(c))

    def test_absent_targets_and_controls_are_preserved(self):
        cases = [case(), case('missing', 'outside'), case('control', None)]
        result = p.summarize(cohort(cases), [observation(c) for c in cases])
        self.assertEqual(result['positive_queries'], 2)
        self.assertEqual(result['control_queries'], 1)
        self.assertEqual(result['candidate_recall'], .5)
        # Identical logits cannot safely distinguish a positive from its control.
        for metrics in result['policies'].values():
            self.assertEqual(metrics['correct_accepted'], 0)
            self.assertEqual(metrics['abstentions'], 3)
            self.assertIsNone(metrics['development_precision'])

    def test_rejects_partial_duplicate_reordered_or_changed_observations(self):
        cases = [case(), case('two')]; rows = [observation(c) for c in cases]
        for invalid in (rows[:1], rows[::-1], [rows[0], rows[0]]):
            with self.assertRaises(ValueError):p.summarize(cohort(cases), invalid)
        changed = copy.deepcopy(cases); changed[0]['query'] += ' Changed.'
        with self.assertRaises(ValueError):p.summarize(cohort(changed), rows)

    def test_policy_replay_rejects_bad_logits_and_candidate_rebinding(self):
        c = case(); rows = observation(c)['evidence']
        for field, value in [('falseLogit', float('inf')), ('trueLogit', True),
                             ('document', 'Changed'), ('key', 'different')]:
            bad = copy.deepcopy(rows); bad[0][field] = value
            with self.assertRaises(ValueError):p.rank_logits(c, bad, 'logit_difference')
        with self.assertRaises(ValueError):p.rank_logits(c, rows[::-1], 'true_logit')
        with self.assertRaises(ValueError):p.rank_logits(c, rows, 'probability')

    def test_no_held_out_cohort_or_duplicate_candidates(self):
        data = cohort([case()]); data['partition'] = 'evaluation'
        with self.assertRaises(ValueError):p.validate_cohort(data)
        data = cohort([case()]); data['cases'][0]['documents'][1]['key'] = 'wrong'
        with self.assertRaises(ValueError):p.validate_cohort(data)

    def test_chunking_preserves_global_ids_and_runs_inference_once_per_chunk(self):
        c = case(); c['documents'] = [{'key': str(i), 'text': 'Document '+str(i)} for i in range(23)]
        class Runtime:
            def __init__(self):self.calls = []; self.last_receipt = {}
            def rerank_evidence(self, query, docs):
                self.calls.append(list(docs)); self.last_receipt = {'call': len(self.calls)}
                return [dict(index=i, document=text, score=float(i), trueLogit=float(i),
                             falseLogit=-float(i), tokenIds=[i], tokenCount=1)
                        for i, text in enumerate(docs)]
        runtime = Runtime(); row = p.collect(runtime, c)
        self.assertEqual(list(map(len, runtime.calls)), [10, 10, 3])
        self.assertEqual([r['index'] for r in row['evidence']], list(range(23)))
        self.assertEqual([r['key'] for r in row['evidence']], [str(i) for i in range(23)])
        self.assertEqual([r['call'] for r in row['receipts']], [1, 2, 3])


if __name__ == '__main__':
    unittest.main()
