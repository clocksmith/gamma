"""Prepare the reviewed 2415 originals through the existing native runner.

This is a fixed request preparer, not an execution engine or variant registry.
The host-only marker projection preserves all original semantic expectations.
Native observation and singleton batching are explicitly versioned successors;
original pre-source evidence and historical observer bytes remain immutable.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from . import imported_qualification as q
from . import request_git_queue04_subset02_oracles as oracle
from .boundary_policy import authorize_before_open
from .known_spec_service import KnownSpecService, _boundary_snapshot

IDS = (2415,)
LANGUAGES = ('javascript', 'python')
DOMAIN = 'request-native2415-v1'
ORACLE_SHA256 = '4c0d510bc631307b5b4d5584d4fcc1fded168beef6f25f046c4e84d59fcc4ddb'
MANIFEST_SHA256 = '9b6d502f8c5e9aedf80e76a71e6d02980499df55e472fb7f48481cf8c870deaa'
SEMANTIC_CASES_SHA256 = 'f6011182ad26f5505741a5ce5a926d0d3deaa84676089182de8978bad622e235'
NATIVE_BATCHES_SHA256 = '5764189135692567fe316c5bcdc39ccf1acd98f52e68829cb70dce02bab902cd'
SOURCE_SHA256 = {2415: {
    'javascript': '9cbb216720ec830c105b27c245a27b362de6bde5930c25afbc02852adfbc1b63',
    'python': 'f5bb395514eb49a02db87e4f1bddde5ded2018daaa8bc618ab997fa93b50031f'}}
BLOB_OIDS = {2415: {'javascript': '5b8efc84cda0224647d3274b8fd285b879ba3972',
                    'python': '2757d9c50240ec915f1f98176d2a898ec7830011'}}
CASE_SHA256 = {2415: '404a4fd05805b39b5e95e851ffc9a96bc9b1f9bb018aae6c940edc1ffd2ff594'}
CASE_COUNT = {2415: 243}
INTERFACES = {'javascript': 'native2415-commonjs-function-solve-v1',
              'python': 'native2415-global-solve-v1'}
EVIDENCE_SHA256 = {
    'oracle-manifest.json': MANIFEST_SHA256,
    'oracle-review.json': 'c5dae660d1e30824333694efe20404b058029e33c36d5b92d211956c98ec5092',
    'pre-source-contract-v1.json': '80b95a2f0b319791aac2a99f82ae15a8f967e02a6e8dc8a3004aa7a82ca308dd',
    'pre-source-contract-review.json': '23f778344ddaf0fd84300b2a72f2f3ade5df428372a3650c5814a8a1422436a7',
    'javascript-acquisition.json': 'b461c244ae9db1b46d9cb386a7541fd14c979625d23cc89a48569ba5cfa1285e',
    'python-acquisition.json': '26268ca3aa1e206a4f8d17b2a716b7e210b168d1bc7a19b9dc3da33d0cdd1882',
    'first-static-review-v1.json': '08cfeec9ab0d0f8613fdb7b430779ad5b8eedee7120ed7212fc458166f61459a',
    'independent-static-review-v1.json': '90914810b073890452ac4a53eda8015708b773fba27a6643a437d8b5418be07e',
    'native-projection-v1.json': '613742b7f5fc9e9ceccbe8b072bd8a2299886e51904c33d8ea300cc97a84f131'}


def original_base(config):
    if (config['catalogue']['sha256'] != '9ab963740caad76bb15d602fb2ab93e2d010f2765605a9b9e63bbaa620dbb329' or
            config['verified_receipts']['sha256'] != '63a3c432f5ec3057dda03a560080f089d70ad4fffa9966a215343d61bd2148fc'):
        raise ValueError('original943 qualification base required')


def validate(pid, args):
    if (type(pid) is not int or pid != 2415 or type(args) is not list or len(args) != 1 or
            type(args[0]) is not dict or set(args[0]) != {'__tree_node__'}):
        raise ValueError('one native perfect-tree marker for identity 2415 required')
    oracle.validate(pid, [args[0]['__tree_node__']])


def project(semantic):
    """Representation only: expected values never enter the native packet."""
    result = []
    for case in semantic:
        if type(case) is not dict or set(case) != {'args', 'compare', 'expected'} or case['compare'] != 'return':
            raise ValueError('exact semantic case shape required')
        oracle.validate(2415, case['args'])
        oracle.validate(2415, [case['expected']])
        if len(case['args'][0]) != len(case['expected']):
            raise ValueError('native projection cannot alter tree size')
        result.append({'args': [{'__tree_node__': list(case['args'][0])}], 'compare': 'return',
                       'expected': {'__tree_node__': list(case['expected'])}})
    return result


def native_batches(cases):
    return [{'offset': offset, 'count': len(batch), 'packet_bytes': len(q.encoded(q.packet(batch, True))),
             'packet_sha256': q.sha(q.encoded(q.packet(batch, True)))}
            for offset, batch in q.batches(cases, 1, True)]


def additional_code():
    if q.file_hash(oracle.__file__) != ORACLE_SHA256:
        raise ValueError('immutable semantic oracle changed')
    paths = [Path(__file__).resolve(), Path(oracle.__file__).resolve()]
    paths += [Path(__file__).with_name(name) for name in
              ('verify_imported_qualification.py', 'verify_imported_semantics.py', 'verify_node_identity.py')]
    return {str(p): q.file_hash(p) for p in paths}


def native_code():
    directory = q.NODE_HARNESS.with_name('imported-node2415-observer-v1')
    paths = [Path(q.__file__).resolve(), directory / 'harness.py', directory / 'harness.cjs']
    paths += [Path(__file__).with_name(name) for name in
              ('node_identity_contracts.py', 'imported_result_contracts.py')]
    closure = {**{str(p): q.file_hash(p) for p in paths}, **additional_code()}
    return {str(Path(name).relative_to(q.SOLVER)): value for name, value in closure.items()}


def pinned(path, pin):
    raw = q.read(path)
    if q.sha(raw) != pin:
        raise ValueError('fixed evidence changed: ' + Path(path).name)
    return raw


def evidence(root):
    return {name: pinned(root / name, pin) for name, pin in EVIDENCE_SHA256.items()}


def interface_contract():
    return {'schema': 'gamma.native2415-interface-successor.v1', 'problem_ids': list(IDS),
            'source_sha256': {str(pid): SOURCE_SHA256[pid] for pid in IDS},
            'prior_pre_source_contract_sha256': EVIDENCE_SHA256['pre-source-contract-v1.json'],
            'declaration_timing': 'post-source exact native interface binding; pre-source semantic contract retained',
            'interfaces': INTERFACES, 'native_code_sha256': native_code(),
            'native_parameters': ['root'], 'constructor_injection': False, 'source_rewriting': False,
            'semantic_cases_sha256': SEMANTIC_CASES_SHA256, 'native_cases_sha256': CASE_SHA256[2415],
            'native_batches_sha256': NATIVE_BATCHES_SHA256, 'maximum_calls_per_batch': 1,
            'projection_only': True, 'node_identity': True, 'comparison_policy': 'problem:2415',
            'original_candidate_bytes_unchanged': True, 'semantic_expectations_unchanged': True,
            'runtime_bounds_unchanged': True, 'automatic_promotion': False}


def approved_interface(root, review_sha256):
    contract_raw = pinned(root / 'interface-contract.json', q.sha(q.encoded(interface_contract())))
    review_raw = pinned(root / 'interface-review.json', review_sha256)
    review = q.decode(review_raw)
    flags = ('independent_review', 'approved', 'original_candidate_bytes_unchanged',
             'semantic_expectations_unchanged', 'runtime_bounds_unchanged',
             'original_pre_source_gap_preserved', 'original_observer_bytes_unchanged')
    if (review.get('schema') != 'gamma.native2415-interface-review.v1' or
            any(review.get(key) is not True for key in flags) or
            not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip() or
            review.get('contract_sha256') != q.sha(contract_raw) or
            review.get('native_code_sha256') != native_code()):
        raise ValueError('independently reviewed native interface binding required')
    return contract_raw, review_raw


def generated(pid, statement, manifest):
    if type(pid) is not int or pid != 2415:
        raise ValueError('identity outside fixed native population')
    semantic, categories = oracle.build_cases(pid, statement)
    row = next(r for r in manifest['records'] if r['problem_id'] == pid)
    legacy = [{'offset': offset, 'count': len(batch), 'packet_bytes': len(q.encoded(q.packet(batch))),
               'packet_sha256': q.sha(q.encoded(q.packet(batch)))} for offset, batch in q.batches(semantic)]
    cases = project(semantic)
    if (len(cases) != CASE_COUNT[pid] or q.sha(q.encoded(semantic)) != SEMANTIC_CASES_SHA256 or
            q.sha(q.encoded(cases)) != CASE_SHA256[pid] or q.sha(q.encoded(categories)) != row['category_sha256'] or
            legacy != row['batches'] or q.sha(q.encoded(legacy)) != row['batch_sha256'] or
            q.sha(q.encoded(native_batches(cases))) != NATIVE_BATCHES_SHA256 or
            manifest['limits'] != q.LIMITS or manifest['max_file'] != q.MAX_FILE or manifest['max_packet'] != q.MAX_PACKET):
        raise ValueError('semantic design, native projection or unchanged bounds drift')
    return cases, categories


def source_bytes(path, pid, language, gate):
    if type(pid) is not int or pid not in IDS or language not in LANGUAGES:
        raise ValueError('source outside fixed identity/language population')
    authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'], language=language)
    raw = q.read(path, 1024 * 1024)
    if (q.sha(raw) != SOURCE_SHA256[pid][language] or
            hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() != BLOB_OIDS[pid][language]):
        raise ValueError('exact original Git source binding differs')
    return raw


def verify_freeze(root, contract, gate):
    jobs = contract.get('jobs', [])
    if (contract.get('selected_problem_ids') != list(IDS) or contract.get('pending') != [] or
            contract.get('automatic_promotion') is not False or contract.get('protected_access') is not False or
            contract.get('additional_code') != additional_code() or contract.get('limits') != q.LIMITS or
            contract.get('max_packet_bytes') != q.MAX_PACKET or
            [(j.get('id'), j.get('language')) for j in jobs] != [(pid, lang) for pid in IDS for lang in LANGUAGES]):
        raise ValueError('fixed two-job population or request bindings differ')
    original_base(q.decode(pinned(contract['service_config'], contract['service_config_sha256'])))
    input_root = contract.get('input_root')
    if not isinstance(input_root, str) or not Path(input_root).is_absolute() or '..' in Path(input_root).parts:
        raise ValueError('explicit original input root required')
    retained = evidence(root / 'evidence')
    approved_interface(root / 'evidence', contract['interface_review_sha256'])
    manifest = q.decode(retained['oracle-manifest.json'])
    for pid in IDS:
        authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'], language='python', payload_kind='statement')
        statement = pinned(root / f'statements/{pid}.md', oracle.DEFINITION_SHA256[pid])
        cases, categories = generated(pid, statement, manifest)
        if (q.read(root / f'tests/{pid}.json') != q.encoded(cases) or
                q.read(root / f'tests/{pid}.categories.json') != q.encoded(categories) or
                q.read(root / f'tests/{pid}.native-batches.json') != q.encoded(native_batches(cases))):
            raise ValueError('frozen test payload differs')
        for job in (j for j in jobs if j['id'] == pid):
            lang = job['language'];suffix = 'js' if lang == 'javascript' else 'py'
            expected = make_job(root, pid, lang, cases, str(Path(input_root) / f'sources/{pid}.{suffix}'))
            if job != expected:
                raise ValueError('fixed source/domain/interface job differs')


def make_job(root, pid, language, cases, original_source):
    if type(pid) is not int or pid not in IDS or language not in LANGUAGES:
        raise ValueError('job outside fixed identity/language population')
    suffix = 'js' if language == 'javascript' else 'py'
    return {'id': pid, 'language': language, 'source': f'sources/{pid}.{suffix}',
            'source_sha256': SOURCE_SHA256[pid][language], 'original_source': original_source,
            'tests': f'tests/{pid}.json', 'tests_raw_sha256': CASE_SHA256[pid],
            'tests_canonical_sha256': q.canonical_tests_hash(cases), 'case_count': CASE_COUNT[pid],
            'statement': {'path': str((root / f'statements/{pid}.md').resolve()), 'sha256': oracle.DEFINITION_SHA256[pid]},
            'domain_validator': DOMAIN, 'comparison_policy': 'problem:2415',
            'source_interface': INTERFACES[language], 'node_identity': True, 'max_cases_per_batch': 1}


def prepare(args):
    runtime_identity = q.runtime(getattr(args, 'node_runtime', None))
    KnownSpecService.from_config(args.config, args.config_sha256)
    config = q.decode(pinned(args.config, args.config_sha256))
    original_base(config)
    gate_spec = config['source_access']['boundary_gate'];gate = q.decode(pinned(gate_spec['path'], gate_spec['sha256']))
    if not {f'leetcode:{pid}' for pid in IDS} <= _boundary_snapshot(gate).authorized:
        raise PermissionError('fixed request population is not currently authorized')
    retained = evidence(args.input_root / 'evidence')
    interface, review = approved_interface(args.input_root / 'evidence', args.interface_review_sha256)
    manifest = q.decode(retained['oracle-manifest.json']);all_cases = {};statements = {};categories = {}
    for pid in IDS:
        authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'], language='python', payload_kind='statement')
        statements[pid] = pinned(args.input_root / f'statements/{pid}.md', oracle.DEFINITION_SHA256[pid])
        all_cases[pid], categories[pid] = generated(pid, statements[pid], manifest)
        if (pinned(args.input_root / f'tests/{pid}.json', CASE_SHA256[pid]) != q.encoded(all_cases[pid]) or
                q.read(args.input_root / f'tests/{pid}.categories.json') != q.encoded(categories[pid])):
            raise ValueError('private packet case bytes differ')
    args.output.mkdir(parents=True, exist_ok=False)
    for directory in ('sources', 'tests', 'statements', 'evidence'):
        (args.output / directory).mkdir()
    for name, raw in {**retained, 'interface-contract.json': interface, 'interface-review.json': review}.items():
        (args.output / 'evidence' / name).write_bytes(raw)
    jobs = []
    for pid in IDS:
        (args.output / f'statements/{pid}.md').write_bytes(statements[pid])
        q.write(args.output / f'tests/{pid}.json', all_cases[pid]);q.write(args.output / f'tests/{pid}.categories.json', categories[pid])
        q.write(args.output / f'tests/{pid}.native-batches.json', native_batches(all_cases[pid]))
        for lang in LANGUAGES:
            suffix = 'js' if lang == 'javascript' else 'py';source = args.input_root / f'sources/{pid}.{suffix}'
            raw = source_bytes(source, pid, lang, gate)
            (args.output / f'sources/{pid}.{suffix}').write_bytes(raw)
            jobs.append(make_job(args.output, pid, lang, all_cases[pid], str(source.resolve())))
    contract = {'schema': 'gamma.imported-independent-execution.v1', 'selected_problem_ids': list(IDS),
                'jobs': jobs, 'pending': [], 'automatic_promotion': False, 'protected_access': False,
                'service_config': str(args.config.resolve()), 'service_config_sha256': args.config_sha256,
                'input_root': str(args.input_root.resolve()),
                'runtime': runtime_identity, 'code': q.code_pins(), 'additional_code': additional_code(),
                'limits': q.LIMITS, 'max_packet_bytes': q.MAX_PACKET, 'interface_review_sha256': args.interface_review_sha256,
                'effects': 'Only odd-depth node values are reversed; identical original root, nodes, links, classes/prototypes and field descriptors; no external IO.',
                'scope': 'Exposed development finite-case qualification only; not universal proof, fresh confirmation or catalogue adoption.'}
    q.write(args.output / 'contract.json', contract)
    return {'jobs': len(jobs), 'cases_per_language': sum(CASE_COUNT.values()), 'contract_sha256': q.file_hash(args.output / 'contract.json')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'input-root', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--interface-review-sha256', required=True)
    parser.add_argument('--node-runtime', type=Path)
    print(q.encoded(prepare(parser.parse_args())).decode(), end='')
