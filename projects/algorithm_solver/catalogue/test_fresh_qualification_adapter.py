import copy
from pathlib import Path
from unittest.mock import patch

import pytest

from . import fresh_qualification_adapter as a
from .catalogue import digest
from . import test_public_foundation_adapter_v2 as prior_tests


def fixture():
    oracle_sha = a.sha(a.bounded_regular_read(Path(a.oracle.__file__).absolute()))
    jobs = [{'id': 301, 'language': lang, 'source_sha256': ('a' if lang == 'javascript' else 'b') * 64,
             'statement': {'sha256': 'c' * 64}, 'tests_raw_sha256': 'd' * 64, 'case_count': 3,
             'domain_validator': 'fresh67-v1', 'comparison_policy': 'set-of-strings'} for lang in a.LANGUAGES]
    contract = {'statement_sha256': 'c' * 64, 'input_validator_sha256': oracle_sha,
                'tests_raw_sha256': 'd' * 64, 'case_count_per_language': 3, 'public_examples': 1,
                'domain_review': {'conclusion': 'accepted'}, 'oracle_review': 'independent exhaustive check',
                'effects': a.EFFECTS, 'comparison_policy': 'set-of-strings', 'caveats': ['finite evidence'],
                'source_review': {j['language']: {'source_sha256': j['source_sha256'],
                    'conclusion': 'accepted', 'complexity_review': 'bounded search',
                    'effects_review': 'readonly inputs'} for j in jobs}}
    freeze = {'jobs': jobs, 'additional_code': {str(Path(a.oracle.__file__).resolve()): oracle_sha},
              'effects': a.EFFECTS, 'pending': [], 'public_examples_checked': {'301': 1}}
    review = {'schema': 'gamma.fresh67-authority-review.v1', 'approval': 'approved',
              'freeze_sha256': 'f' * 64, 'approved_ids': [301], 'contracts': {'301': contract},
              'independent_of_candidate_authorship': True, 'independent_of_oracle_authorship': True,
              'reviewer': 'independent reviewer', 'normative_statement_scope': 'pinned mirror'}
    return freeze, review


def check(freeze, review):
    with patch.object(a.oracle, 'IDS', [301]):
        return a.check_review(review, freeze, 'f' * 64)


def test_complete_source_specific_review():
    freeze, review = fixture()
    assert check(freeze, review) == review['contracts']


@pytest.mark.parametrize('mutation', ['missing-language', 'duplicate-job', 'wrong-source', 'wrong-statement',
    'wrong-tests', 'wrong-effects', 'wrong-validator', 'missing-complexity', 'missing-approval', 'partial-review'])
def test_fail_closed_review_bindings(mutation):
    freeze, review = fixture()
    contract = review['contracts']['301']
    if mutation == 'missing-language': freeze['jobs'].pop()
    elif mutation == 'duplicate-job': freeze['jobs'].append(copy.deepcopy(freeze['jobs'][0]))
    elif mutation == 'wrong-source': contract['source_review']['python']['source_sha256'] = '0' * 64
    elif mutation == 'wrong-statement': contract['statement_sha256'] = '0' * 64
    elif mutation == 'wrong-tests': contract['tests_raw_sha256'] = '0' * 64
    elif mutation == 'wrong-effects': contract['effects'] = 'any mutation'
    elif mutation == 'wrong-validator': contract['input_validator_sha256'] = '0' * 64
    elif mutation == 'missing-complexity': del contract['source_review']['python']['complexity_review']
    elif mutation == 'missing-approval': review['independent_of_oracle_authorship'] = False
    elif mutation == 'partial-review': review['approved_ids'] = []
    with pytest.raises(ValueError): check(freeze, review)


def test_replacements_retain_receipts_and_reject_protected():
    universe, catalogue, receipts, replacements, additions = prior_tests.PublicFoundationAdoptionV2().replacement_fixture()
    old = copy.deepcopy((universe, catalogue, receipts))
    _, retained, _ = a.replace_canonicals(universe, catalogue, receipts, replacements, additions)
    assert all(retained[k] == v for k, v in receipts.items())
    assert (universe, catalogue, receipts) == old
    universe['protected_problem_ids'].append('a')
    with pytest.raises(ValueError): a.replace_canonicals(universe, catalogue, receipts, replacements, additions)


def test_validator_requires_receipt_bound_domain_and_rejects_string_array():
    contract = {'numeric_problem_id': 3838, 'input_validator': {'lane': 'fresh67-v1',
        'module_sha256': a.sha(a.bounded_regular_read(Path(a.oracle.__file__).absolute())),
        'numeric_problem_id': 3838, 'entrypoint': 'validate', 'required_before_candidate_execution': True}}
    impl = {'status': 'qualified', 'evidence_class': 'normative-typed-effects',
        'problem_contract_sha256': digest(contract), 'provenance': {'fresh_qualification': {'problem_contract': contract}}}
    assert a.validate_inputs(impl, [['abc'], [1]*26])['accepted']
    with pytest.raises(ValueError): a.validate_inputs(impl, ['abc', [1]*26])
    impl['problem_contract_sha256'] = '0' * 64
    with pytest.raises(ValueError): a.validate_inputs(impl, [['abc'], [1]*26])


def test_existing_output_never_overwritten(tmp_path):
    (tmp_path / 'sentinel').write_text('keep')
    with pytest.raises(ValueError): a.persist({}, tmp_path)
    assert (tmp_path / 'sentinel').read_text() == 'keep'
