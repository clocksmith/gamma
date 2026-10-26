"""Explicit, independently reviewed fresh-case adoption into a new private config.

The operator pins the complete plan. Replaying observations grants no promotion
by itself. This module never activates a service or executes candidate code.
"""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path

from . import imported_qualification as q
from . import qualification_fresh_cases as oracle
from . import verify_imported_qualification as verifier
from .boundary_policy import authorize_before_open
from .catalogue import BINDINGS, digest, validate
from .known_spec_service import KnownSpecService
from .public_batch_adapter import bounded_regular_read, fields, pinned, replace_canonicals, sha

HERE = Path(__file__).resolve().parent
EFFECTS = 'read-only arguments; no mutable return-to-input aliases'
LANGUAGES = ('javascript', 'python')


def check_review(review, freeze, freeze_sha256):
    jobs = freeze['jobs']
    ids = sorted({j['id'] for j in jobs})
    if (any(type(j['id']) is not int for j in jobs) or
            {(j['id'], j['language']) for j in jobs} != {(p, l) for p in ids for l in LANGUAGES} or
            len(jobs) != len(ids) * 2 or ids != sorted(oracle.IDS)):
        raise ValueError('complete fixed fresh dual-language population required')
    if (review.get('schema') != 'gamma.fresh67-authority-review.v1' or
            review.get('approval') != 'approved' or review.get('freeze_sha256') != freeze_sha256 or
            review.get('independent_of_candidate_authorship') is not True or
            review.get('independent_of_oracle_authorship') is not True or
            not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip() or
            not review.get('normative_statement_scope') or review.get('approved_ids') != ids or
            set(review.get('contracts', {})) != {str(p) for p in ids}):
        raise ValueError('complete independently pinned authority review required')
    oracle_sha = sha(bounded_regular_read(Path(oracle.__file__).absolute()))
    if freeze.get('additional_code', {}).get(str(Path(oracle.__file__).resolve())) != oracle_sha:
        raise ValueError('frozen domain module identity differs')
    if freeze.get('effects') != EFFECTS or freeze.get('pending') != []:
        raise ValueError('unsupported effects or partial freeze')
    for job in jobs:
        contract = review['contracts'][str(job['id'])]
        source = contract.get('source_review', {}).get(job['language'], {})
        policy = 'set-of-strings' if job['id'] == 301 else 'permutation-of-chars' if job['id'] == 3692 else 'exact'
        if (job.get('domain_validator') != 'fresh67-v1' or job.get('comparison_policy') != policy or
                contract.get('comparison_policy') != policy or contract.get('effects') != EFFECTS or
                contract.get('input_validator_sha256') != oracle_sha or
                contract.get('statement_sha256') != job['statement']['sha256'] or
                contract.get('tests_raw_sha256') != job['tests_raw_sha256'] or
                contract.get('case_count_per_language') != job['case_count'] or
                contract.get('public_examples') != freeze['public_examples_checked'][str(job['id'])] or
                contract.get('domain_review', {}).get('conclusion') != 'accepted' or
                not contract.get('oracle_review') or source.get('source_sha256') != job['source_sha256'] or
                any(not isinstance(source.get(k), str) or not source[k].strip()
                    for k in ('conclusion', 'complexity_review', 'effects_review')) or
                not isinstance(contract.get('caveats'), list) or not contract['caveats'] or
                any(not isinstance(c, str) or not c for c in contract['caveats'])):
            raise ValueError('per-ID statement/domain/source/effect review binding differs')
    return review['contracts']


def replay(report_path):
    # Separate module instances: anchored reads do not mutate the running service
    # or another agent's execution modules.
    def load(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    runner = load('catalogue._fresh_adoption_runner', Path(q.__file__))
    runner.read = lambda path, maximum=q.MAX_FILE: bounded_regular_read(Path(path).absolute(), maximum_bytes=maximum)
    check = load('catalogue._fresh_adoption_verifier', Path(verifier.__file__))
    check.q = runner
    return check.verify(Path(report_path))


def adopt_plan(plan_path, trusted_plan_sha256):
    plan, _ = pinned({'path': str(plan_path), 'sha256': trusted_plan_sha256})
    fields(plan, ('schema', 'config', 'freeze', 'report', 'verification', 'review', 'verifier_sha256'))
    if plan['schema'] != 'gamma.fresh67-adoption-plan.v1':
        raise ValueError('unsupported adoption plan')
    if sha(bounded_regular_read(Path(verifier.__file__).absolute())) != plan['verifier_sha256']:
        raise ValueError('explicit independent verifier code pin differs')
    values = {k: pinned(plan[k])[0] for k in ('config', 'freeze', 'report', 'verification', 'review')}
    config, freeze, report, verification, review = (values[k] for k in ('config', 'freeze', 'report', 'verification', 'review'))
    KnownSpecService.from_config(plan['config']['path'], plan['config']['sha256'])
    if (freeze['service_config'] != plan['config']['path'] or freeze['service_config_sha256'] != plan['config']['sha256'] or
            str(Path(plan['freeze']['path']).parent) != report['freeze'] or
            Path(plan['freeze']['path']).name != 'contract.json' or
            report['freeze_sha256'] != plan['freeze']['sha256'] or
            verification['verifier_sha256'] != plan['verifier_sha256'] or
            verification['report_sha256'] != plan['report']['sha256'] or
            verification['freeze_sha256'] != plan['freeze']['sha256']):
        raise ValueError('explicit configuration/freeze/report/verifier identity differs')
    contracts = check_review(review, freeze, plan['freeze']['sha256'])
    universe = pinned(config['universe'])[0]
    catalogue = pinned(config['catalogue'])[0]
    receipts = pinned(config['verified_receipts'])[0]
    validate(universe, catalogue, receipts)
    gate = pinned(config['source_access']['boundary_gate'])[0]
    source_bytes = {}
    for job in freeze['jobs']:
        pid, language = job['id'], job['language']
        gid = f'leetcode:{pid}'
        authorize_before_open(gid, gate['artifact_paths'], gate['trusted_hashes'], language=language)
        authorize_before_open(gid, gate['artifact_paths'], gate['trusted_hashes'], language=language, payload_kind='statement')
        expected_name = f"sources/{pid}.{'js' if language == 'javascript' else 'py'}"
        if job['source'] != expected_name or job['tests'] != f'tests/{pid}.json' or job['statement']['problem_id'] != gid:
            raise ValueError('source/test/statement identity differs')
        source = bounded_regular_read(Path(report['freeze']) / expected_name, maximum_bytes=1024**2)
        statement = bounded_regular_read(job['statement']['path'])
        if sha(source) != job['source_sha256'] or sha(statement) != job['statement']['sha256']:
            raise ValueError('reviewed exact source or statement changed')
        source_bytes[(gid, language)] = source
    reproduced = replay(plan['report']['path'])
    if reproduced != verification or verification.get('verified') is not True:
        raise ValueError('actual independent observation replay differs')
    outcomes = verification['outcomes']
    if ([(o['id'], o['language']) for o in outcomes] != [(j['id'], j['language']) for j in freeze['jobs']] or
            any(o['passed'] is not True or o['failure_count'] != 0 for o in outcomes)):
        raise ValueError('complete all-cases-passed outcomes required')
    return build_successor(plan, trusted_plan_sha256, config, freeze, review, contracts,
                           universe, catalogue, receipts, source_bytes, verification)


def build_successor(plan, plan_sha256, config, freeze, review, contracts, universe,
                    catalogue, receipts, source_bytes, verification, *, lane='fresh67-v1'):
    """Shared receipt construction after lane-specific authority and replay gates."""
    provenance_key = 'fresh_qualification' if lane == 'fresh67-v1' else 'admitted_qualification'
    rows = {r['problem_id']: r for r in catalogue['problems']}
    replacements, additions, descriptors = {}, {}, {}
    for job, outcome in zip(freeze['jobs'], verification['outcomes']):
        if outcome['passed'] is not True:
            continue
        pid, language = job['id'], job['language']; gid = f'leetcode:{pid}'
        if (outcome['source_sha256'] != job['source_sha256'] or outcome['tests_raw_sha256'] != job['tests_raw_sha256'] or
                outcome['cases'] != job['case_count']):
            raise ValueError('source-specific verdict differs')
        reviewed = contracts[str(pid)]
        contract = {'schema': 'gamma.reviewed-fresh-contract.v1' if lane == 'fresh67-v1' else 'gamma.reviewed-imported-contract.v1', 'numeric_problem_id': pid,
            'reviewed_statement_contract': reviewed, 'statement_identity': job['statement'],
            'normative_statement_scope': review['normative_statement_scope'],
            'authority_review_sha256': plan['review']['sha256'], 'qualification_freeze_sha256': plan['freeze']['sha256'],
            'input_validator': {'lane': lane, 'module_sha256': reviewed['input_validator_sha256'],
                'numeric_problem_id': pid, 'entrypoint': 'validate', 'required_before_candidate_execution': True}}
        interface = {'schema': 'gamma.call-interface.v1', 'entrypoint': 'solve', 'arguments': 'ordered-positional', 'typed_contract': digest(contract)}
        runtime = {'language': language, 'runtime_closure': freeze['runtime'], 'limits': freeze['limits'],
            'max_packet_bytes': freeze['max_packet_bytes'], 'code': freeze['code']}
        effects = {'policy': freeze['effects'], 'comparison_policy': job['comparison_policy'], 'code': freeze['code'],
            'verifier_sha256': plan['verifier_sha256'], 'review_sha256': plan['review']['sha256']}
        old = rows[gid]['implementations'][language]
        provenance = {provenance_key: {'problem_contract': contract, 'source_provenance': job,
            'report_sha256': plan['report']['sha256'], 'verification_sha256': plan['verification']['sha256'],
            'review_sha256': plan['review']['sha256'], 'case_count': job['case_count']},
            'previous_canonical': {'implementation_sha256': digest(old), 'receipt_sha256': old.get('receipt_sha256'),
                'base_catalogue_sha256': config['catalogue']['sha256']},
            'historical_receipts_unchanged': True, 'source_publication_authorized': False}
        caveats = reviewed['caveats'] + ['Run the frozen domain validator before candidate execution.',
            'Source acquisition does not establish recognition, publication, or current-serving execution qualification.']
        impl = {'status': 'qualified', 'evidence_class': 'normative-typed-effects',
            'canonical_variant_id': language + ':' + job['source_sha256'], 'source_sha256': job['source_sha256'],
            'problem_contract_sha256': digest(contract), 'interface': interface, 'interface_sha256': digest(interface),
            'runtime_sha256': digest(runtime), 'tests_sha256': job['tests_raw_sha256'], 'effects_sha256': digest(effects),
            'contract_scope': f'Reviewed pinned statement domain for problem {pid}; ordered solve interface and local effects only.',
            'caveats': caveats, 'provenance': provenance}
        receipt = {k: impl[k] for k in (*BINDINGS, 'canonical_variant_id', 'evidence_class', 'contract_scope', 'caveats')}
        receipt.update(problem_id=gid, language=language, verdict='qualified', independent_verifier=True,
            provenance_sha256=digest(provenance), original_independent_verification_sha256=plan['verification']['sha256'],
            review_sha256=plan['review']['sha256'], per_problem_case_count=job['case_count'])
        rid = digest(receipt); impl['receipt_sha256'] = rid
        replacements[(gid, language)] = impl; additions[rid] = receipt
        descriptors[f'{language}:{pid}'] = {'problem_contract': contract, 'runtime': runtime, 'effects': effects}
    updated, retained, summary = replace_canonicals(universe, catalogue, receipts, replacements, additions)
    return {'catalogue': updated, 'verified_receipts': retained, 'summary': summary, 'config': config,
        'source_locators': pinned(config['source_access']['locators'])[0], 'source_bytes': {key: source_bytes[key] for key in replacements},
        'binding_descriptors': descriptors, 'audit': {'schema': 'gamma.fresh67-adoption.v1' if lane == 'fresh67-v1' else 'gamma.imported358-adoption.v1',
            'plan_sha256': plan_sha256, 'previous_receipts_preserved': len(receipts),
            'adopted_source_language_pairs': len(replacements), 'new_receipts': len(additions),
            'activated': False, 'candidate_executions': 0, 'source_publication_authorized': False}}


def persist(result, output):
    """Write a new private successor only; no existing service pointer changes."""
    output = Path(output).absolute()
    if output.exists() or output.is_symlink() or output.parent.resolve() != output.parent:
        raise ValueError('new canonical private output directory required')
    output.mkdir(mode=0o700)
    config = copy.deepcopy(result['config']); locators = copy.deepcopy(result['source_locators'])
    (output / 'sources').mkdir(mode=0o700)
    for (gid, language), raw in result['source_bytes'].items():
        suffix = 'js' if language == 'javascript' else 'py'
        path = output / 'sources' / f'{gid.split(":")[1]}.{suffix}'
        with path.open('xb') as stream:
            stream.write(raw)
        path.chmod(0o600)
        locators['problems'].setdefault(gid, {})[language] = str(path)
    def write(name, value):
        raw = q.encoded(value); path = output / name
        with path.open('xb') as stream:
            stream.write(raw)
        path.chmod(0o600)
        return {'path': str(path), 'sha256': sha(raw)}
    config['catalogue'] = write('catalogue.json', result['catalogue'])
    config['verified_receipts'] = write('verified-receipts.json', result['verified_receipts'])
    config['source_access']['locators'] = write('source-locators.json', locators)
    config['source_access']['source_roots'].append(str(output / 'sources'))
    config['source_access']['authorized_problem_ids'] = sorted(set(config['source_access']['authorized_problem_ids']) | {p for p, _ in result['source_bytes']})
    write('binding-descriptors.json', result['binding_descriptors'])
    write('adoption-receipt.json', result['audit'])
    spec = write('config.json', config)
    KnownSpecService.from_config(spec['path'], spec['sha256'])
    return {'config': spec, 'summary': result['summary'], 'audit': result['audit']}


def validate_inputs(implementation, args):
    contract = implementation.get('provenance', {}).get('fresh_qualification', {}).get('problem_contract', {})
    predicate = contract.get('input_validator', {})
    pid = contract.get('numeric_problem_id')
    if (implementation.get('status') != 'qualified' or implementation.get('evidence_class') != 'normative-typed-effects' or
            digest(contract) != implementation.get('problem_contract_sha256') or pid not in oracle.IDS or
            predicate != {'lane': 'fresh67-v1', 'module_sha256': sha(bounded_regular_read(Path(oracle.__file__).absolute())),
                'numeric_problem_id': pid, 'entrypoint': 'validate', 'required_before_candidate_execution': True}):
        raise ValueError('frozen fresh input predicate identity mismatch')
    oracle.validate(pid, args)
    return {'accepted': True, 'candidate_executed': False, 'problem_contract_sha256': digest(contract)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(persist(adopt_plan(args.plan, args.plan_sha256), args.output)))


if __name__ == '__main__':
    main()
