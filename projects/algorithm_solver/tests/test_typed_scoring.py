"""Software recovery tests; fixture verdicts are not solver qualification."""
import copy
import fcntl
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from algsolve.synth import mine, typed_codec
from algsolve.synth.typed_scoring import score_frozen, write_bytes_once, write_json_once


class FrozenScoringTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.routes = ['raw','constrained','nearest_training_graph']
        self.candidate = {'schema':'fixture','version':1}
        self.tests = [{'args':[3],'expected':3}]
        self.requests = [{'uid':f'fixture:{i}','learning_split':split,
                          'provenance':{'independent_tests_sha256':mine.digest(self.tests)}}
                         for i,split in enumerate(['development_fit','development_audit'])]
        self.decisions = [{'uid':p['uid'],'split':p['learning_split'],
                           'routes':{r:{'route':r,'decision':'abstain','reason':'fixture_invalid',
                                        'source':None,'infrastructure_failure':False}
                                     for r in self.routes}} for p in self.requests]
        write_json_once(self.root/'candidate.json',self.candidate)
        write_json_once(self.root/'setup.json',{'scope':'fixture'})
        write_bytes_once(self.root/'captures.jsonl',b'{}\n')
        self.save_decisions()
        self.calls = []

    def save_decisions(self):
        (self.root/'decisions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in self.decisions))

    def loader(self,pair):
        self.assertTrue((self.root/'scoring/seal.json').is_file())
        self.assertEqual(len(self.decisions),2)
        return copy.deepcopy(self.tests)

    def scorer(self,pair,decision,tests):
        self.calls.append((pair['uid'],decision['route']))
        return {**decision,'independent':None,'accepted_correct':False,'wrong_acceptance':False}

    def run_scoring(self,scorer=None,loader=None):
        return score_frozen(self.root,self.requests,self.candidate,self.routes,
                            loader or self.loader,scorer or self.scorer)

    def test_qualification_test_hash_is_distinct_from_graph_hash(self):
        # Pair qualification uses sorted JSON with ordinary separators. Graphs
        # and receipt objects use a different, compact serialization.
        import hashlib
        expected = hashlib.sha256(b'[{"args": [3], "expected": 3}]').hexdigest()
        self.assertEqual(self.requests[0]['provenance']['independent_tests_sha256'], expected)
        self.assertNotEqual(expected, typed_codec.digest(self.tests))
        self.assertEqual(len(self.run_scoring()), 2)

    def test_graph_hash_cannot_replace_qualified_test_authority(self):
        self.requests[0]['provenance']['independent_tests_sha256'] = typed_codec.digest(self.tests)
        with self.assertRaisesRegex(ValueError, 'scoring authority'):
            self.run_scoring()
        self.assertEqual(self.calls, [])

    def test_interruption_retains_each_route_and_resumes_only_missing(self):
        def interrupt(pair,decision,tests):
            if len(self.calls)==2:
                raise RuntimeError('injected interruption')
            return self.scorer(pair,decision,tests)
        with self.assertRaisesRegex(RuntimeError,'injected interruption'):
            self.run_scoring(interrupt)
        existing = {p.name:p.read_bytes() for p in (self.root/'scoring').glob('0000-*.json')}
        self.assertEqual(len(existing),2)
        rows = self.run_scoring()
        self.assertEqual(len(rows),2)
        self.assertEqual(len(self.calls),6)
        self.assertEqual(len(set(self.calls)),6)
        for name,data in existing.items():
            self.assertEqual((self.root/'scoring'/name).read_bytes(),data)
        self.assertEqual(self.run_scoring(),rows)
        self.assertEqual(len(self.calls),6)

    def test_missing_duplicate_reordered_or_extra_decisions_never_open_tests(self):
        original = copy.deepcopy(self.decisions)
        mutations = [original[:1],[original[0],original[0]],original[::-1],original+[original[0]]]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.decisions = mutation; self.save_decisions()
                with self.assertRaises(ValueError):
                    self.run_scoring(loader=lambda p:self.fail('opened tests for incomplete decisions'))
        self.assertFalse((self.root/'scoring/seal.json').exists())

    def test_route_denominator_and_protected_partition_fail_closed(self):
        self.decisions[0]['routes'].pop('raw'); self.save_decisions()
        with self.assertRaisesRegex(ValueError,'route denominator'):
            self.run_scoring()
        self.requests[0]['learning_split']='protected'
        with self.assertRaisesRegex(ValueError,'development cohort'):
            self.run_scoring()
        self.assertEqual(self.calls,[])

    def test_decision_and_candidate_changes_reject_resumption(self):
        self.run_scoring()
        for name in ('candidate.json','captures.jsonl','setup.json','decisions.jsonl'):
            path=self.root/name; original=path.read_bytes()
            path.write_bytes(original+b' ')
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.run_scoring(loader=lambda p:self.fail('tests opened after drift'))
            path.write_bytes(original)
        self.assertEqual(len(self.calls),6)

    def test_changed_test_authority_or_receipt_cannot_be_promoted(self):
        with self.assertRaisesRegex(ValueError,'scoring authority'):
            self.run_scoring(loader=lambda p:[{'args':[3],'expected':4}])
        self.assertEqual(self.calls,[])
        self.run_scoring()
        receipt=self.root/'scoring/0000-raw.json'
        data=json.loads(receipt.read_text()); data['result']['accepted_correct']=True
        receipt.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'receipt identity'):
            self.run_scoring()

    def test_scorer_cannot_change_decision_or_frozen_files(self):
        def change_decision(pair,decision,tests):
            decision['decision']='answered'
            return self.scorer(pair,decision,tests)
        with self.assertRaisesRegex(ValueError,'changed a frozen route'):
            self.run_scoring(change_decision)
        self.assertFalse((self.root/'scoring/0000-raw.json').exists())
        def change_file(pair,decision,tests):
            with (self.root/'decisions.jsonl').open('a') as stream: stream.write('\n')
            return self.scorer(pair,decision,tests)
        with self.assertRaisesRegex(ValueError,'changed during scoring'):
            self.run_scoring(change_file)
        self.assertFalse((self.root/'scoring/0000-raw.json').exists())

    def test_atomic_publication_does_not_leave_partial_or_overwrite_evidence(self):
        path=self.root/'new.json'
        with patch('algsolve.synth.typed_scoring.os.link',side_effect=OSError('interrupted publish')):
            with self.assertRaises(OSError): write_json_once(path,{'one':1})
        self.assertFalse(path.exists())
        self.assertEqual(list(self.root.glob('.new.json-*')),[])
        write_json_once(path,{'one':1})
        original=path.read_bytes()
        with self.assertRaises(FileExistsError): write_json_once(path,{'two':2})
        self.assertEqual(path.read_bytes(),original)

    def test_simultaneous_scorer_rejected(self):
        directory=self.root/'scoring'; directory.mkdir()
        with (directory/'lock').open('a') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaisesRegex(RuntimeError,'Another scorer'):
                self.run_scoring()
        self.assertEqual(self.calls,[])



    def test_scorer_cannot_mutate_test_authority_or_publish_its_verdict(self):
        def mutate(pair, decision, tests):
            tests[0]['expected'] = 999
            return self.scorer(pair, decision, tests)
        with self.assertRaisesRegex(ValueError, 'changed the frozen tests'):
            self.run_scoring(mutate, loader=lambda pair: self.tests)
        self.assertEqual(self.tests, [{'args': [3], 'expected': 3}])
        self.assertEqual(list((self.root/'scoring').glob('0000-*.json')), [])

    def test_later_route_mutation_preserves_prior_receipt_and_resumes_same_tests(self):
        def mutate_second(pair, decision, tests):
            if decision['route'] == 'constrained':
                tests[0]['args'].append(999)
            return self.scorer(pair, decision, tests)
        with self.assertRaisesRegex(ValueError, 'changed the frozen tests'):
            self.run_scoring(mutate_second)
        raw = self.root/'scoring/0000-raw.json'
        original = raw.read_bytes()
        self.assertFalse((self.root/'scoring/0000-constrained.json').exists())
        observed = []
        def unchanged(pair, decision, tests):
            observed.append(copy.deepcopy(tests))
            return self.scorer(pair, decision, tests)
        self.assertEqual(len(self.run_scoring(unchanged)), 2)
        self.assertEqual(observed, [self.tests] * 5)
        self.assertEqual(raw.read_bytes(), original)
        self.assertEqual(self.calls.count(('fixture:0', 'raw')), 1)


if __name__=='__main__': unittest.main()
