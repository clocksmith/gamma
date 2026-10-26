import copy
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from . import admitted_qualification_adapter as a
from .catalogue import digest


def fixture(tmp_path):
    evidence = tmp_path / 'review.json'; evidence.write_text('{"reviewed":true}')
    jobs, contracts = [], {}
    module_hashes = {str(Path(m.__file__).resolve()): a.sha(a.bounded_regular_read(Path(m.__file__).absolute()))
                     for m in (a.admission, a.clean)}
    for pid in range(1, 359):
        statement = {'sha256': 'b'*64, 'problem_id': f'leetcode:{pid}'}
        contract = {'statement_sha256': 'b'*64, 'input_validator_sha256': module_hashes[str(Path(a.domain_module(pid).__file__).resolve())],
                    'comparison_policy': f'problem:{pid}', 'effects': a.EFFECTS,
                    'tests_raw_sha256': 'c'*64, 'case_count_per_language': 5, 'public_examples': 2,
                    'domain_review': {'conclusion': 'accepted'}, 'oracle_review': 'independent review',
                    'caveats': ['finite evidence'], 'source_review': {}}
        for lang in a.shared.LANGUAGES:
            job = {'id': pid, 'language': lang, 'statement': statement, 'source_sha256': 'a'*64,
                   'tests_raw_sha256': 'c'*64, 'case_count': 5, 'comparison_policy': f'problem:{pid}',
                   'domain_validator': 'imported358-v1', 'node_identity': pid in (814, 2074, 2807),
                   'max_cases_per_batch': 1 if pid in (814, 1681, 1755, 2074, 2807) else 32}
            jobs.append(job)
            contract['source_review'][lang] = {'source_sha256': 'a'*64, 'conclusion': 'reviewed',
                'complexity_review': 'bounded', 'effects_review': 'readonly', 'reviewer': 'separate reviewer'}
        contracts[str(pid)] = contract
    freeze = {'jobs': jobs, 'pending': [], 'original_freeze_sha256': a.ORIGINAL_SHA,
              'effects': a.EFFECTS, 'additional_code': module_hashes, 'protected_access': False,
              'automatic_promotion': False, 'public_examples_checked': {str(p): 2 for p in range(1, 359)}}
    review = {'schema': 'gamma.imported358-authority-review.v1', 'approval': 'approved',
              'freeze_sha256': 'f'*64, 'approved_ids': list(range(1, 359)), 'reviewer': 'independent coordinator',
              'independent_of_candidate_authorship': True, 'independent_of_oracle_authorship': True,
              'normative_statement_scope': 'pinned mirror', 'contracts': contracts,
              'evidence_pins': [{'path': str(evidence), 'sha256': a.sha(evidence.read_bytes())}]}
    return freeze, review, copy.deepcopy({'jobs': jobs})


def test_complete_review(tmp_path):
    freeze, review, original = fixture(tmp_path)
    assert len(a.check_review(review, freeze, 'f'*64, original)) == 358


@pytest.mark.parametrize('change', ['partial', 'duplicate', 'statement', 'source', 'validator', 'reviewer', 'ledger-authority', 'batch-profile', 'identity-profile'])
def test_rejects_partial_or_substituted_evidence(tmp_path, change):
    freeze, review, original = fixture(tmp_path)
    if change == 'partial': freeze['jobs'].pop()
    elif change == 'duplicate': freeze['jobs'][-1] = freeze['jobs'][0]
    elif change == 'statement': freeze['jobs'][0]['statement']['problem_id'] = 'leetcode:9999'
    elif change == 'source': review['contracts']['1']['source_review']['python']['source_sha256'] = '0'*64
    elif change == 'validator': review['contracts']['1']['input_validator_sha256'] = '0'*64
    elif change == 'reviewer': del review['contracts']['1']['source_review']['python']['reviewer']
    elif change == 'ledger-authority': review['evidence_pins'][0]['sha256'] = '0'*64
    elif change == 'batch-profile': freeze['jobs'][0]['max_cases_per_batch'] = True
    elif change == 'identity-profile': freeze['jobs'][0]['node_identity'] = True
    with pytest.raises(ValueError): a.check_review(review, freeze, 'f'*64, original)


def test_any_failed_outcome_refuses_atomic_adoption():
    jobs = [{'id': 1, 'language': lang, 'source_sha256': 'a'*64, 'tests_raw_sha256': 'b'*64, 'case_count': 5}
            for lang in a.shared.LANGUAGES]
    outcomes = [{**job, 'cases': 5, 'passed': index == 0, 'failure_count': index}
                for index, job in enumerate(jobs)]
    with pytest.raises(ValueError, match='all-or-nothing'):
        a.check_outcomes(jobs, {'outcomes': outcomes})
    successful = copy.deepcopy(outcomes)
    successful[1].update(passed=True, failure_count=0)
    assert a.check_outcomes(jobs, {'outcomes': successful}) == {('leetcode:1', lang) for lang in a.shared.LANGUAGES}
    outcomes[1]['passed'] = True
    with pytest.raises(ValueError): a.check_outcomes(jobs, {'outcomes': outcomes})
    with pytest.raises(ValueError): a.check_outcomes(jobs, {'outcomes': outcomes[:1]})


def test_shared_builder_preserves_old_slots_and_receipts_and_copies_only_passes():
    universe = {'schema': 'gamma.catalogue-universe.v1', 'eligible_problem_ids': ['leetcode:1'],
                'protected_problem_ids': [], 'metadata_sha256': '1'*64, 'eligibility_policy': 'test'}
    catalogue = {'schema': 'gamma.dual-language-catalogue.v2', 'universe_sha256': digest(universe),
                 'evidence_policy': {'schema': 'gamma.catalogue-evidence-policy.v1', 'allowed_classes': ['normative-typed-effects'], 'scope_rule': 'exact-bound-contract-only'},
                 'problems': [{'problem_id': 'leetcode:1', 'implementations': {lang: {'status': 'blocked', 'reason': 'pending'} for lang in a.shared.LANGUAGES}}]}
    legacy = {'retained': 'historical receipt'}; receipts = {digest(legacy): legacy}
    jobs = [{'id': 1, 'language': lang, 'source_sha256': 'a'*64, 'tests_raw_sha256': 'b'*64, 'case_count': 5,
             'statement': {'sha256': 'c'*64}, 'comparison_policy': 'problem:1'} for lang in a.shared.LANGUAGES]
    freeze = {'jobs': jobs, 'effects': a.EFFECTS, 'runtime': {}, 'limits': {}, 'max_packet_bytes': 100, 'code': {}}
    outcomes = [{**job, 'cases': 5, 'passed': index == 0, 'failure_count': index} for index, job in enumerate(jobs)]
    config = {'catalogue': {'sha256': 'd'*64}, 'source_access': {'locators': {}}}
    plan = {key: {'sha256': 'e'*64} for key in ('review', 'freeze', 'report', 'verification')}; plan['verifier_sha256'] = 'f'*64
    contracts = {'1': {'input_validator_sha256': 'c'*64, 'caveats': ['finite evidence']}}
    before = copy.deepcopy((catalogue, receipts))
    with patch.object(a.shared, 'pinned', return_value=({'schema': 'gamma.dual.source-locators.v1', 'problems': {}}, b'')):
        result = a.shared.build_successor(plan, 'f'*64, config, freeze, {'normative_statement_scope': 'pinned mirror'}, contracts,
            universe, catalogue, receipts, {('leetcode:1', lang): b'source' for lang in a.shared.LANGUAGES},
            {'outcomes': outcomes}, lane='imported358-v1')
    assert (catalogue, receipts) == before
    assert result['catalogue']['problems'][0]['implementations']['python'] == {'status': 'blocked', 'reason': 'pending'}
    assert result['verified_receipts'][digest(legacy)] == legacy
    assert set(result['source_bytes']) == {('leetcode:1', 'javascript')}
    assert result['audit']['adopted_source_language_pairs'] == 1
