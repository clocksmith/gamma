"""Adopt only independently reviewed, passing statement-admitted implementations.

The externally pinned final review binds exact sources, domains, observations,
corrections and supplemental evidence. Historical receipts are never rewritten.
"""
import argparse
import json
from pathlib import Path

from . import fresh_qualification_adapter as shared
from . import imported_case_admission as admission
from . import imported_clean_domains as clean
from . import imported_qualification as q
from . import verify_imported_qualification as verifier
from .boundary_policy import authorize_before_open
from .catalogue import digest, validate
from .known_spec_service import KnownSpecService
from .public_batch_adapter import bounded_regular_read, fields, pinned, sha

ORIGINAL_SHA = '956e15f937b9f457014eaac7d91939209ba3901f3f4f5f9e93b53f41ed037e43'
EFFECTS = 'read-only arguments and no return aliases, except876requires original middle-node identity'


def domain_module(pid):
    return admission if pid in admission.DOMAIN_IDS else clean


def check_review(review, freeze, freeze_sha256, original):
    jobs = freeze['jobs']; ids = sorted({job['id'] for job in jobs})
    pairs = [(j['id'], j['language']) for j in jobs]
    expected = [(j['id'], j['language']) for j in original['jobs']]
    if (len(ids) != 358 or len(pairs) != 716 or len(set(pairs)) != len(pairs) or
            set(pairs) != set(expected) or
            set(pairs) != {(pid, lang) for pid in ids for lang in shared.LANGUAGES} or
            any(type(pid) is not int for pid in ids)):
        raise ValueError('complete original source-language population required')
    if (review.get('schema') != 'gamma.imported358-authority-review.v1' or
            review.get('approval') != 'approved' or review.get('freeze_sha256') != freeze_sha256 or
            review.get('approved_ids') != ids or
            review.get('independent_of_candidate_authorship') is not True or
            review.get('independent_of_oracle_authorship') is not True or
            not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip() or
            not review.get('normative_statement_scope') or
            set(review.get('contracts', {})) != {str(pid) for pid in ids}):
        raise ValueError('complete final independent authority review required')
    if (freeze.get('original_freeze_sha256') != ORIGINAL_SHA or freeze.get('pending') != [] or
            freeze.get('effects') != EFFECTS or freeze.get('protected_access') is not False or
            freeze.get('automatic_promotion') is not False):
        raise ValueError('unsupported population/effect/authority contract')
    evidence = review.get('evidence_pins')
    if not isinstance(evidence, list) or not evidence:
        raise ValueError('independent review provenance pins required')
    for spec in evidence:
        pinned(spec)
    originals = {(j['id'], j['language']): j for j in original['jobs']}
    for job in jobs:
        pid, language = job['id'], job['language']; contract = review['contracts'][str(pid)]
        module = domain_module(pid); module_path = str(Path(module.__file__).resolve())
        module_sha = sha(bounded_regular_read(module_path))
        source = contract.get('source_review', {}).get(language, {})
        if (job.get('domain_validator') != 'imported358-v1' or job.get('comparison_policy') != f'problem:{pid}' or
                freeze.get('additional_code', {}).get(module_path) != module_sha or
                contract.get('input_validator_sha256') != module_sha or
                contract.get('comparison_policy') != job['comparison_policy'] or
                contract.get('effects') != EFFECTS or
                contract.get('statement_sha256') != job['statement']['sha256'] or
                job['statement'] != originals[(pid, language)]['statement'] or
                contract.get('tests_raw_sha256') != job['tests_raw_sha256'] or
                contract.get('case_count_per_language') != job['case_count'] or
                contract.get('public_examples') != freeze['public_examples_checked'][str(pid)] or
                contract.get('domain_review', {}).get('conclusion') != 'accepted' or not contract.get('oracle_review') or
                source.get('source_sha256') != job['source_sha256'] or
                any(not isinstance(source.get(key), str) or not source[key].strip()
                    for key in ('conclusion', 'complexity_review', 'effects_review', 'reviewer')) or
                not isinstance(contract.get('caveats'), list) or not contract['caveats'] or
                any(not isinstance(caveat, str) or not caveat for caveat in contract['caveats'])):
            raise ValueError('per-ID statement/domain/source/effect/case review differs')
    return review['contracts']


def check_outcomes(jobs, verification):
    outcomes = verification.get('outcomes', [])
    if ([(o['id'], o['language']) for o in outcomes] != [(j['id'], j['language']) for j in jobs] or
            any(type(o.get('passed')) is not bool or type(o.get('failure_count')) is not int or
                o['failure_count'] < 0 or o['passed'] != (o['failure_count'] == 0) for o in outcomes)):
        raise ValueError('complete source-specific passed/failed outcomes required')
    for job, outcome in zip(jobs, outcomes):
        if (outcome.get('source_sha256') != job['source_sha256'] or
                outcome.get('tests_raw_sha256') != job['tests_raw_sha256'] or
                outcome.get('cases') != job['case_count']):
            raise ValueError('outcome source/case binding differs')
    return {(f"leetcode:{o['id']}", o['language']) for o in outcomes if o['passed']}


def adopt_plan(plan_path, trusted_plan_sha256):
    plan, _ = pinned({'path': str(plan_path), 'sha256': trusted_plan_sha256})
    fields(plan, ('schema', 'config', 'original', 'freeze', 'report', 'verification', 'review', 'verifier_sha256'))
    if plan['schema'] != 'gamma.imported358-adoption-plan.v1' or plan['original']['sha256'] != ORIGINAL_SHA:
        raise ValueError('explicit original population and adoption plan required')
    if sha(bounded_regular_read(Path(verifier.__file__).absolute())) != plan['verifier_sha256']:
        raise ValueError('explicit independent verifier code pin differs')
    values = {key: pinned(plan[key])[0] for key in ('config', 'original', 'freeze', 'report', 'verification', 'review')}
    config, original, freeze, report, verification, review = (values[k] for k in ('config', 'original', 'freeze', 'report', 'verification', 'review'))
    KnownSpecService.from_config(plan['config']['path'], plan['config']['sha256'])
    if (freeze['service_config'] != plan['config']['path'] or freeze['service_config_sha256'] != plan['config']['sha256'] or
            str(Path(plan['freeze']['path']).parent) != report['freeze'] or Path(plan['freeze']['path']).name != 'contract.json' or
            report['freeze_sha256'] != plan['freeze']['sha256'] or
            verification['verifier_sha256'] != plan['verifier_sha256'] or
            verification['report_sha256'] != plan['report']['sha256'] or verification['freeze_sha256'] != plan['freeze']['sha256']):
        raise ValueError('configuration/freeze/report/verifier identity differs')
    contracts = check_review(review, freeze, plan['freeze']['sha256'], original)
    universe = pinned(config['universe'])[0]; catalogue = pinned(config['catalogue'])[0]
    receipts = pinned(config['verified_receipts'])[0]; validate(universe, catalogue, receipts)
    gate = pinned(config['source_access']['boundary_gate'])[0]
    sources = {}
    for job in freeze['jobs']:
        pid, language = job['id'], job['language']; gid = f'leetcode:{pid}'
        authorize_before_open(gid, gate['artifact_paths'], gate['trusted_hashes'], language=language)
        authorize_before_open(gid, gate['artifact_paths'], gate['trusted_hashes'], language=language, payload_kind='statement')
        suffix = 'js' if language == 'javascript' else 'py'
        if (job['source'] != f'sources/{pid}.{suffix}' or job['tests'] != f'tests/{pid}.json' or
                job['statement']['problem_id'] != gid):
            raise ValueError('source/test/statement identity differs')
        root = Path(report['freeze'])
        source = bounded_regular_read(root / job['source'], maximum_bytes=1024**2)
        if (sha(source) != job['source_sha256'] or
                sha(bounded_regular_read(job['statement']['path'])) != job['statement']['sha256'] or
                sha(bounded_regular_read(root / 'admission' / f'{pid}.json')) != job['admission_sha256']):
            raise ValueError('reviewed exact source/statement/admission ledger changed')
        sources[(gid, language)] = source
    reproduced = shared.replay(plan['report']['path'])
    if reproduced != verification or verification.get('verified') is not True:
        raise ValueError('actual independent observation replay differs')
    passing = check_outcomes(freeze['jobs'], verification)
    result = shared.build_successor(plan, trusted_plan_sha256, config, freeze, review, contracts,
        universe, catalogue, receipts, sources, verification, lane='imported358-v1')
    if set(result['source_bytes']) != passing:
        raise ValueError('nonpassing implementation entered successor')
    result['audit']['failed_source_language_pairs_retained_without_adoption'] = len(freeze['jobs']) - len(passing)
    return result


def validate_inputs(implementation, args):
    contract = implementation.get('provenance', {}).get('admitted_qualification', {}).get('problem_contract', {})
    pid = contract.get('numeric_problem_id')
    if type(pid) is not int:
        raise ValueError('numeric reviewed problem identity required')
    module = domain_module(pid)
    if (implementation.get('status') != 'qualified' or implementation.get('evidence_class') != 'normative-typed-effects' or
            digest(contract) != implementation.get('problem_contract_sha256') or
            contract.get('input_validator') != {'lane': 'imported358-v1',
                'module_sha256': sha(bounded_regular_read(Path(module.__file__).absolute())),
                'numeric_problem_id': pid, 'entrypoint': 'validate', 'required_before_candidate_execution': True}):
        raise ValueError('frozen admitted input predicate identity differs')
    module.validate(pid, args)
    return {'accepted': True, 'candidate_executed': False, 'problem_contract_sha256': digest(contract)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(shared.persist(adopt_plan(args.plan, args.plan_sha256), args.output)))


if __name__ == '__main__':
    main()
