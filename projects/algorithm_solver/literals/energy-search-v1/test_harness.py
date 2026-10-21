"""Mechanism tests only. No candidate program is executed or qualified here."""
import copy
from dataclasses import replace
import json
import math
from pathlib import Path
import tempfile
import unittest

import harness as h
from fixtures import synthetic_dataset, comparison_pool, SEED_FIXTURE, SEED_FIXTURE_SHA
from tiny_reference import support_and_reference


class SpyScorer:
    model_id = 'unit-test-spy-not-a-trained-model'
    model_bytes = 0
    scorer_version = 'constant-spy-v1'
    scorer_seed = 20261021
    scorer_artifact_sha256 = h.identity({'unit-test-spy':'constant-only-v1'})
    trained_source_hashes = ()

    def __init__(self, data, value=0):
        self.calls = 0
        self.value = value
        self.training_manifest_sha256 = h.identity({'dataset_id':data['corpus_id'], 'split':data['split'], 'trained_source_hashes':[]})

    def energy(self, features):
        self.calls += 1
        assert 'package_bits' not in features and 'selections' not in features
        return self.value


class HarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.inventory = synthetic_dataset()
        cls.pieces, cls.state = comparison_pool(cls.data,cls.inventory,'compression','mined-only',6)

    def test_dataset_schema_and_frozen_identity(self):
        self.assertTrue(h.validate_dataset(self.data))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'data.json';path.write_bytes(h.canonical(self.data))
            self.assertEqual(h.load_dataset(path,h.raw_hash(path.read_bytes())),self.data)
            with self.assertRaises(h.Ineligible):h.load_dataset(path,'0'*64)
        for filename in ('dataset.schema.json','states.schema.json'):
            self.assertEqual(json.loads((h.ROOT/filename).read_text())['$schema'],'https://json-schema.org/draft/2020-12/schema')

    def test_source_contract_and_hidden_side_channel_rejected(self):
        for field,value in [('source_sha256','0'*64),('contract_sha256','0'*64),('implicit_code',True),('operand_bits',6),('control_bits',6)]:
            data=copy.deepcopy(self.data);next(iter(data['variants'].values()))[field]=value
            with self.subTest(field=field),self.assertRaises(h.Ineligible):h.validate_dataset(data)

    def test_self_consistent_weaker_contract_cannot_compete(self):
        data=copy.deepcopy(self.data)
        key='fixture-a:original'; variant=data['variants'][key]
        contract=copy.deepcopy(data['contracts'][variant['contract_id']])
        contract['domain']='Weaker domain that omits required cases'
        data['contracts']['weaker']=contract
        variant['contract_id']='weaker';variant['contract_sha256']=h.identity(contract)
        data['qualifications'][variant['qualification_id']]['contract_sha256']=variant['contract_sha256']
        spy=SpyScorer(data)
        with self.assertRaisesRegex(h.Ineligible,'different contracts'):
            h.compare(data,self.pieces,[self.state],spy,max_evaluations=1,max_cpu_seconds=2)
        self.assertEqual(spy.calls,0)
        with self.assertRaisesRegex(h.Ineligible,'different contracts'):
            list(h.neighbors(data,self.pieces,self.state,limit=12))

    def cross_language_fixture(self):
        data=copy.deepcopy(self.data)
        original=data['variants']['fixture-a:original']
        variant=copy.deepcopy(original);variant['id']='fixture-a:python'
        variant['language']='python';variant['source']='def demonstration(value):\n    return value\n'
        variant['source_sha256']=h.raw_hash(variant['source'].encode());variant['helper_spans']=[]
        contract=copy.deepcopy(data['contracts'][original['contract_id']]);contract['language']='python'
        variant['contract_id']='python-contract';variant['contract_sha256']=h.identity(contract)
        data['contracts'][variant['contract_id']]=contract
        qualification=copy.deepcopy(data['qualifications'][original['qualification_id']])
        qualification['source_sha256']=variant['source_sha256'];qualification['contract_sha256']=variant['contract_sha256']
        variant['qualification_id']='python-synthetic';data['qualifications'][variant['qualification_id']]=qualification
        data['variants'][variant['id']]=variant
        return data,variant

    def test_neighborhood_does_not_rewrite_across_languages(self):
        data,variant=self.cross_language_fixture()
        self.assertTrue(h.validate_dataset(data))
        for move,_ in h.neighbors(data,self.pieces,self.state,limit=200):
            if move['kind']=='rewrite':self.assertNotEqual(move['rewrite'][1],variant['id'])
        report=support_and_reference(data,self.pieces,self.state,())
        self.assertEqual(report['enumerated_states'],4)

    def test_comparison_cannot_switch_language(self):
        data,variant=self.cross_language_fixture()
        first=replace(self.state,choices=(('fixture-a','fixture-a:original'),))
        second=replace(first,choices=(('fixture-a',variant['id']),))
        spy=SpyScorer(data)
        receipt=h.compare(data,self.pieces,[first,second],spy,max_evaluations=2,max_cpu_seconds=2)
        self.assertEqual(receipt['eligible'],1);self.assertEqual(spy.calls,1)
        self.assertIn('language/contract',receipt['rejected'][0]['reason'])

    def test_direct_cost_feature_and_reference_reject_stale_source(self):
        data=copy.deepcopy(self.data)
        data['variants'][self.state.choices[0][1]]['source']+=' '
        calls=(lambda:h.exact_measure(data,self.pieces,self.state),
               lambda:h.features(data,self.pieces,self.state),
               lambda:support_and_reference(data,self.pieces,self.state,()))
        for call in calls:
            with self.subTest(call=call),self.assertRaisesRegex(h.Ineligible,'source hash'):
                call()

    def test_exclusion_and_alias_gates(self):
        variant=next(iter(self.data['variants'].values()))
        for field,value in [('problem_ids',variant['problem_id']),('family_ids',variant['family_id']),('source_sha256',variant['source_sha256']),('aliases',variant['aliases'][0])]:
            data=copy.deepcopy(self.data);data['excluded'][field].append(value)
            with self.subTest(field=field),self.assertRaises(h.Ineligible):h.validate_dataset(data)

    def test_problem_and_source_split_leakage(self):
        for field in ('problem','source'):
            data=copy.deepcopy(self.data);a=data['variants']['fixture-a:original'];b=data['variants']['fixture-test:original']
            if field=='problem':b['problem_id']=a['problem_id']
            else:b['source']=a['source'];b['source_sha256']=a['source_sha256']
            with self.subTest(field=field),self.assertRaises(h.Ineligible):h.validate_dataset(data)

    def test_alias_split_leakage(self):
        data=copy.deepcopy(self.data)
        data['variants']['fixture-test:original']['aliases'].append('fixture-a')
        with self.assertRaisesRegex(h.Ineligible,'alias split leakage'):h.validate_dataset(data)

    def test_alias_and_canonical_identity_share_one_namespace(self):
        data=copy.deepcopy(self.data)
        original=data['variants']['fixture-a:original'];held=data['variants']['fixture-test:original']
        for variant in data['variants'].values():
            if variant['problem_id']==original['problem_id']:variant['aliases']=[]
        held['aliases'].append(original['problem_id'])
        with self.assertRaisesRegex(h.Ineligible,'alias split leakage'):h.validate_dataset(data)
        data=copy.deepcopy(self.data)
        data['excluded']['problem_ids'].append('protected-alias-only')
        data['variants']['fixture-a:original']['aliases'].append('protected-alias-only')
        with self.assertRaisesRegex(h.Ineligible,'protected alias'):h.validate_dataset(data)

    def test_required_qualification_fields_fail_closed(self):
        data=copy.deepcopy(self.data);variant=data['variants'][self.state.choices[0][1]]
        del data['qualifications'][variant['qualification_id']]['candidate_execution']
        with self.assertRaisesRegex(h.Ineligible,'envelope fields missing'):h.exact_measure(data,self.pieces,self.state)
        schema=json.loads((h.ROOT/'dataset.schema.json').read_text())['$defs']['qualification']
        self.assertIn('candidate_execution',schema['allOf'][0]['then']['required'])
        self.assertEqual(set(schema['allOf'][1]['then']['required']),{'independent_reviewed','tests_passed','tests_total','runtime_sha256','proof_files'})

    def test_unqualified_cannot_reach_energy(self):
        data=copy.deepcopy(self.data)
        qid=data['variants'][self.state.choices[0][1]]['qualification_id']
        for gate in h.GATES:
            data['qualifications'][qid]['gates']={g:g!=gate for g in h.GATES}
            spy=SpyScorer(data)
            receipt=h.compare(data,self.pieces,[self.state],spy,max_evaluations=1,max_cpu_seconds=2)
            self.assertEqual(spy.calls,0);self.assertEqual(receipt['eligible'],0)
            self.assertFalse(receipt['rejected'][0]['energy_called'])

    def test_real_envelope_missing_proof_is_ineligible(self):
        data=copy.deepcopy(self.data);data['evidence_class']='exposed-development'
        variant=data['variants'][self.state.choices[0][1]]
        q=data['qualifications'][variant['qualification_id']]
        q.update(evidence_class='exposed-development',independent_reviewed=True,tests_passed=1,tests_total=1,runtime_sha256='a'*64,proof_files=[{'path':str(h.ROOT/'does-not-exist'),'sha256':'0'*64}])
        with self.assertRaisesRegex(h.Ineligible,'unavailable'):h.qualification(data,variant)

    def test_helpers_framing_and_packet_accounting(self):
        result=h.exact_measure(self.data,self.pieces,self.state)
        self.assertEqual(result['coverage'],2)
        expected_dictionary=8+sum(4+len(self.pieces[k].text.encode()) for k in self.state.piece_ids)
        self.assertEqual(result['dictionary_bytes'],expected_dictionary)
        for row in result['rows']:
            self.assertEqual(row['framing_bits'],328)
            self.assertEqual(row['packet_bytes'],41+math.ceil(row['selections']*6/8))
            self.assertEqual(row['helper_bytes'],155)
        self.assertEqual(result['package_bits'],8*(result['dictionary_bytes']+result['packet_bytes']))
        self.assertEqual(result['package_with_decoder_bits'],result['package_bits']+8*result['decoder_bytes'])

    def test_full_source_decode_and_widths(self):
        counts=[]
        for width in (6,7,8):
            result=h.exact_measure(self.data,self.pieces,replace(self.state,width=width))
            counts.append(result['selections'])
            for row in result['rows']:
                self.assertEqual(row['payload_bits'],row['selections']*width)
        self.assertEqual(len(set(counts)),1)

    def test_utf8_and_newlines_are_fully_stored(self):
        data=copy.deepcopy(self.data)
        for variant in data['variants'].values():
            if variant['family_id'] not in ('synthetic-a','synthetic-b'):continue
            variant['source']+='// λ\n'
            variant['source_sha256']=h.raw_hash(variant['source'].encode())
            data['qualifications'][variant['qualification_id']]['source_sha256']=variant['source_sha256']
        h.validate_dataset(data)
        pieces,state=comparison_pool(data,self.inventory,'compression','mined-only',7)
        result=h.exact_measure(data,pieces,state)
        self.assertGreater(result['dictionary_utf8_bytes'],sum(len(pieces[k].text) for k in state.piece_ids))
        for row in result['rows']:
            source=data['variants'][row['variant_id']]['source']
            self.assertEqual(row['source_bytes'],len(source.encode()))

    def test_unreachable_fails_not_finite_sentinel(self):
        pieces=self.pieces
        selected=tuple(k for k in self.state.piece_ids if pieces[k].text!='{')
        with self.assertRaisesRegex(h.Ineligible,'unreachable'):h.exact_measure(self.data,pieces,replace(self.state,piece_ids=selected))

    def test_whole_program_unknown_and_wrong_track_rejected(self):
        variant=self.data['variants'][self.state.choices[0][1]];text=variant['source'];key=h.raw_hash(text.encode())
        pieces=dict(self.pieces);pieces[key]=h.CandidatePiece(key,text,'compression',(variant['id'],))
        with self.assertRaisesRegex(h.Ineligible,'whole-program'):h.exact_measure(self.data,pieces,replace(self.state,piece_ids=(key,)))
        with self.assertRaises(h.Ineligible):h.exact_measure(self.data,self.pieces,replace(self.state,piece_ids=('unknown',)))
        with self.assertRaises(h.Ineligible):h.exact_measure(self.data,self.pieces,replace(self.state,track='readable'))

    def test_dictionary_duplicate_cap_and_identity(self):
        with self.assertRaises(h.Ineligible):h.exact_measure(self.data,self.pieces,replace(self.state,piece_ids=self.state.piece_ids*2))
        with self.assertRaises(h.Ineligible):h.exact_measure(self.data,self.pieces,replace(self.state,width=5))
        key=self.state.piece_ids[0];pieces=dict(self.pieces);pieces[key]=replace(pieces[key],text='not-the-hash')
        with self.assertRaises(h.Ineligible):h.exact_measure(self.data,pieces,self.state)

    def test_partial_and_complete_text_are_not_solved(self):
        problem,key=self.state.choices[0];text=self.data['variants'][key]['source']
        ids=tuple(h.raw_hash(c.encode()) for c in text)
        for count in (1,len(ids)):
            partial=h.PartialAssembly(problem,key,ids[:count],h.raw_hash(text[:count].encode()),() if count==len(ids) else ('remaining-text',))
            result=h.validate_partial(self.data,self.pieces,partial,self.state)
            self.assertFalse(result['qualified_solution'])
            self.assertEqual(result['complete'],count==len(ids))
            with self.assertRaises(h.Ineligible):h.exact_measure(self.data,self.pieces,partial)

    def test_neighborhood_is_deterministic_and_covers_four_moves(self):
        first=list(h.neighbors(self.data,self.pieces,self.state,limit=12));second=list(h.neighbors(self.data,self.pieces,self.state,limit=12))
        self.assertEqual(first,second);self.assertEqual(len(first),12)
        self.assertEqual({move['kind'] for move,_ in first},{'add','delete','swap','rewrite'})
        for _,state in first:self.assertLessEqual(len(state.piece_ids),64)

    def test_comparison_budget_and_matching(self):
        spy=SpyScorer(self.data)
        states=[self.state,replace(self.state,width=7),replace(self.state,choices=self.state.choices[:1])]
        receipt=h.compare(self.data,self.pieces,states,spy,max_evaluations=3,max_cpu_seconds=2)
        self.assertEqual(receipt['exact_evaluation_attempts'],3);self.assertEqual(receipt['eligible'],1)
        self.assertEqual(spy.calls,1);self.assertEqual(receipt['learned_scorer_calls'],1)
        one=h.compare(self.data,self.pieces,states,None,max_evaluations=1,max_cpu_seconds=2)
        self.assertEqual(one['exact_evaluation_attempts'],1)

    def test_training_source_and_manifest_leakage(self):
        spy=SpyScorer(self.data);spy.trained_source_hashes=(self.data['variants']['fixture-test:original']['source_sha256'],)
        with self.assertRaisesRegex(h.Ineligible,'training leakage'):h.compare(self.data,self.pieces,[self.state],spy,max_evaluations=1,max_cpu_seconds=2)
        spy=SpyScorer(self.data);spy.training_manifest_sha256='0'*64
        with self.assertRaisesRegex(h.Ineligible,'manifest'):h.compare(self.data,self.pieces,[self.state],spy,max_evaluations=1,max_cpu_seconds=2)

    def test_test_derived_candidate_leakage(self):
        pieces=dict(self.pieces);key=h.raw_hash('{'.encode());piece=pieces[key]
        pieces[key]=replace(piece,provenance=piece.provenance+('fixture-test:original',))
        spy=SpyScorer(self.data);result=h.compare(self.data,pieces,[self.state],spy,max_evaluations=1,max_cpu_seconds=2)
        self.assertEqual(spy.calls,0);self.assertIn('leakage',result['rejected'][0]['reason'])

    def test_nonfinite_energy_invalidates_comparison(self):
        with self.assertRaisesRegex(ValueError,'nonfinite'):h.compare(self.data,self.pieces,[self.state],SpyScorer(self.data,float('nan')),max_evaluations=1,max_cpu_seconds=2)

    def test_baseline_exact_minimum_over_same_candidates(self):
        states=[self.state]+[state for _,state in h.neighbors(self.data,self.pieces,self.state,limit=12)]
        result=h.compare(self.data,self.pieces,states,SpyScorer(self.data),max_evaluations=13,max_cpu_seconds=2)
        expected=min(result['records'],key=lambda r:(r['labels']['package_bits'],r['labels']['input_bits'],r['state_id']))
        self.assertEqual(result['exact_best'],expected['state_id'])
        self.assertGreaterEqual(result['top1_package_bit_regret'],0)
        self.assertFalse(result['training_performed']);self.assertEqual(result['candidate_programs_executed'],0)

    def test_actual_seed_provenance_never_claims_qualification(self):
        self.assertEqual(self.inventory['qualified_components'],0)
        self.assertEqual(h.raw_hash(SEED_FIXTURE.read_bytes()),SEED_FIXTURE_SHA)
        for seed in self.inventory['seeds']:
            self.assertTrue(seed['receipt_needed'])
            self.assertEqual(h.raw_hash(seed['text'].encode()),seed['sha256'])
            for witness in seed['witnesses']:
                self.assertEqual(set(witness),{'key','source_sha256','qualified'})
                self.assertEqual(len(witness['source_sha256']),64)
                self.assertFalse(witness['qualified'])

    def test_human_seed_baseline_is_explicit_and_helpers_charged(self):
        for track in h.TRACKS:
            pieces,state=comparison_pool(self.data,self.inventory,track,'human-plus-mined',6)
            helper=self.inventory['seeds'][-1]['text'];key=h.raw_hash(helper.encode())
            self.assertIn(key,state.piece_ids)
            measured=h.exact_measure(self.data,pieces,state)
            self.assertGreaterEqual(measured['dictionary_utf8_bytes'],len(helper.encode()))
            self.assertEqual(measured['whole_program_entries'],0)

    def test_designed_only_empty_eligible_retains_denominator(self):
        for track in h.TRACKS:
            pieces,state=comparison_pool(self.data,self.inventory,track,'designed-only',6)
            self.assertTrue(all(len(piece.text)>1 for piece in pieces.values()))
            states=[state]+[child for _,child in h.neighbors(self.data,pieces,state,limit=8)]
            spy=SpyScorer(self.data)
            result=h.compare(self.data,pieces,states,spy,max_evaluations=9,max_cpu_seconds=2)
            self.assertIsNone(result['exact_best']);self.assertIsNone(result['predicted_best'])
            self.assertIsNone(result['top1_package_bit_regret'])
            self.assertEqual(result['best_coverage'],0);self.assertEqual(result['coverage_denominator'],2)
            self.assertEqual(result['eligible'],0);self.assertEqual(spy.calls,0)
            self.assertEqual(len(result['rejected']),result['exact_evaluation_attempts'])

    def test_tiny_exhaustive_and_support_reference(self):
        pieces,initial=comparison_pool(self.data,self.inventory,'compression','human-plus-mined',6)
        additions=tuple(sorted(set(initial.piece_ids)-set(self.state.piece_ids)))
        report=support_and_reference(self.data,pieces,self.state,additions)
        self.assertEqual(report['enumerated_states'],2**len(additions)*4)
        self.assertEqual(len(report['support_matrix']),len(additions))
        self.assertTrue(all(row['distinct_problem_coverage']==2 for row in report['support_matrix']))
        self.assertGreaterEqual(report['greedy_gap_to_enumerated_joint_bits'],0)
        self.assertFalse(report['semantic_dependencies_inferred']);self.assertFalse(report['candidate_execution'])


if __name__=='__main__':unittest.main()
