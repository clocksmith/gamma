"""Prepare only the reviewed 2110/2221 originals through the existing runner.

This is a fixed request preparer, not an execution engine or variant registry.
The direct-function interface is an explicit post-source successor; original
pre-source evidence and its observed interface gap remain immutable.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from . import imported_qualification as q
from . import request_git_queue02_subset01_oracles as oracle
from .boundary_policy import authorize_before_open
from .known_spec_service import KnownSpecService, _boundary_snapshot

IDS = (2110, 2221)
LANGUAGES = ('javascript', 'python')
DOMAIN = 'request-git-subset01-v1'
ORACLE_SHA256 = '2635ef559ee19de6ce456f5e07ce669f7311d4cfbdb2b84056402d9157c080d3'
MANIFEST_SHA256 = '760d801ceecb43d9b4a3dbd0eb8f0da46b757eeef410ab45c0a539cefb7080f2'
SOURCE_SHA256 = {
    2110: {'javascript': 'bf873e2e58ad0f4bd062390a24887762a329fc0608a0f716bb16458f693ecfa5',
           'python': 'bb311b163f3f0db864a4ceaf3183fc7905fb1af04e04f934dfe660e18f2db86b'},
    2221: {'javascript': 'bbf0d6cda5138c6fa021b5a3af267ab2ff60665af4d3e046330f766da818a255',
           'python': '16fc98aa5ea7e5a8dc23404e4ec0a6d663c1cc9e2137f6ceb8c3289a6685cc7b'},
}
BLOB_OIDS = {
    2110: {'javascript': '6987279a68075911c6ee806f5cfec8d819b908c8', 'python': 'cf13e94bc526e474dd03ef7904c9d7034a59f075'},
    2221: {'javascript': 'c5621d396a51835437b6bf38ee10af4ed07b3bcd', 'python': '3368c1b8e7aabe9e8043c71943683f2e9d96001d'},
}
CASE_SHA256 = {2110: 'f764a2395f895f92f6b0643dc11641f68d168d3fb3a9af11fcb34f972f4f9b97',
               2221: 'f3d5201baf5a582df748aebbf7c5da7e510205dd5c6e450402c52a84d04b05a2'}
CASE_COUNT = {2110: 1101, 2221: 1613}
EVIDENCE_SHA256 = {
    'oracle-manifest.json': MANIFEST_SHA256,
    'oracle-review.json': '10806f22406acf566bd319a8bf2ee2fcc9c7a1cb2b52994b93eb01f11ee33d30',
    'pre-source-contract-v1.json': 'f2627d8aa8fbbda09ab85dfaa66966b5721e9af3b4d8f68c3024b085be99c8a5',
    'pre-source-contract-review.json': '6e03870cf49054ef55fce8dfd9e96ef27ea2f7608b4a4be3083e6083944bced1',
    'source-acquisition-v1.json': '5c087729d7c1cffaed224cad449cc6ad7ae689b5d90baadfab085bf6fb7be4b6',
    'first-static-review-v1.json': '6b6f605642737dba752742d6fd278e51f9e0149464d7e24a04192f91ea7a69e2',
    'independent-static-review-v1.json': 'adaa5a96b91c9281d36524d8b46c038e70c81c364bcccfb95907cbb2de0c1346',
}
OLD_LOADER_SHA256 = '55ff4173f9dab55de26dcfe502f60b33ecac96fd3ec9689b150cba58daa4b547'
FUNCTION_LOADER_SHA256 = 'b4811fa56db9e34efd62a2543f93f9277ebda90b739b4a2c029bb7e04606635f'


def original_base(config):
    if (config['catalogue']['sha256'] != '9ab963740caad76bb15d602fb2ab93e2d010f2765605a9b9e63bbaa620dbb329' or
            config['verified_receipts']['sha256'] != '63a3c432f5ec3057dda03a560080f089d70ad4fffa9966a215343d61bd2148fc'):
        raise ValueError('original943 qualification base required')


def validate(pid, args):
    oracle.validate(pid, args)


def additional_code():
    if q.file_hash(oracle.__file__) != ORACLE_SHA256:
        raise ValueError('immutable subset oracle changed')
    return {str(Path(__file__).resolve()): q.file_hash(__file__), str(Path(oracle.__file__).resolve()): ORACLE_SHA256}


def pinned(path, pin):
    raw = q.read(path)
    if q.sha(raw) != pin:
        raise ValueError('fixed evidence changed: ' + Path(path).name)
    return raw


def evidence(root):
    return {name: pinned(root / name, pin) for name, pin in EVIDENCE_SHA256.items()}


def interface_contract():
    return {'schema': 'gamma.git-subset01-interface-successor.v1', 'problem_ids': list(IDS),
            'source_sha256': {str(pid): SOURCE_SHA256[pid] for pid in IDS},
            'prior_pre_source_contract_sha256': EVIDENCE_SHA256['pre-source-contract-v1.json'],
            'declaration_timing': 'post-source observed-interface successor; not retroactive pre-source approval',
            'javascript': 'commonjs-function-solve-v1', 'python': 'global-solve-v1',
            'javascript_call': 'Native CommonJS direct callable export; Reflect.apply(exported, undefined, ordered_args)',
            'ordered_parameters': {str(pid): list(oracle.PARAMETERS[pid]) for pid in IDS},
            'old_object_loader_sha256': OLD_LOADER_SHA256, 'new_function_loader_sha256': FUNCTION_LOADER_SHA256,
            'effects_and_domain_unchanged': True, 'original_candidate_bytes_unchanged': True,
            'cases_unchanged': True, 'runtime_bounds_unchanged': True, 'automatic_promotion': False}


def approved_interface(root, review_sha256):
    contract_raw = pinned(root / 'interface-contract.json', q.sha(q.encoded(interface_contract())))
    review_raw = pinned(root / 'interface-review.json', review_sha256)
    review = q.decode(review_raw)
    if (review.get('schema') != 'gamma.git-subset01-interface-review.v1' or
            review.get('independent_review') is not True or not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip() or
            review.get('approved') is not True or review.get('contract_sha256') != q.sha(contract_raw) or
            review.get('original_candidate_bytes_unchanged') is not True or review.get('effects_and_domain_unchanged') is not True or
            review.get('original_pre_source_gap_preserved') is not True or
            review.get('old_object_loader_sha256') != OLD_LOADER_SHA256 or review.get('new_function_loader_sha256') != FUNCTION_LOADER_SHA256):
        raise ValueError('independently reviewed post-source interface successor required')
    if (q.file_hash(q.COMMONJS_HARNESS) != OLD_LOADER_SHA256 or
            q.file_hash(q.COMMONJS_HARNESS.with_name('function-harness.cjs')) != FUNCTION_LOADER_SHA256):
        raise ValueError('reviewed loader bytes changed')
    return contract_raw, review_raw


def generated(pid, statement, manifest):
    cases, categories = oracle.build_cases(pid, statement)
    row = next(r for r in manifest['records'] if r['problem_id'] == pid)
    groups = [{'offset': offset, 'count': len(batch), 'packet_bytes': len(q.encoded(q.packet(batch)))}
              for offset, batch in q.batches(cases)]
    if (len(cases) != CASE_COUNT[pid] or q.sha(q.encoded(cases)) != CASE_SHA256[pid] or
            q.sha(q.encoded(categories)) != row['category_sha256'] or groups != row['batches'] or
            manifest['limits'] != q.LIMITS or manifest['max_file'] != q.MAX_FILE or manifest['max_packet'] != q.MAX_PACKET):
        raise ValueError('independent case design or unchanged bounds drift')
    for case in cases:
        validate(pid, case['args'])
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
        raise ValueError('fixed four-job population or request bindings differ')
    original_base(q.decode(pinned(contract['service_config'], contract['service_config_sha256'])))
    input_root = contract.get('input_root')
    if not isinstance(input_root, str) or not Path(input_root).is_absolute() or '..' in Path(input_root).parts:
        raise ValueError('explicit original input root required')
    retained = evidence(root / 'evidence')
    approved_interface(root / 'evidence', contract['interface_review_sha256'])
    manifest = q.decode(retained['oracle-manifest.json'])
    for pid in IDS:
        authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'], language='python', payload_kind='statement')
        statement = pinned(root / f'statements/{pid}.md', oracle.STATEMENT_SHA256[pid])
        cases, categories = generated(pid, statement, manifest)
        if (q.read(root / f'tests/{pid}.json') != q.encoded(cases) or
                q.read(root / f'tests/{pid}.categories.json') != q.encoded(categories)):
            raise ValueError('frozen test payload differs')
        for job in (j for j in jobs if j['id'] == pid):
            lang = job['language'];suffix = 'js' if lang == 'javascript' else 'py'
            expected = make_job(root, pid, lang, cases, str(Path(input_root) / f'sources/{pid}.{suffix}'))
            if job != expected:
                raise ValueError('fixed source/domain/interface job differs')


def make_job(root, pid, language, cases, original_source):
    suffix = 'js' if language == 'javascript' else 'py'
    return {'id': pid, 'language': language, 'source': f'sources/{pid}.{suffix}',
            'source_sha256': SOURCE_SHA256[pid][language], 'original_source': original_source,
            'tests': f'tests/{pid}.json', 'tests_raw_sha256': CASE_SHA256[pid],
            'tests_canonical_sha256': q.canonical_tests_hash(cases), 'case_count': CASE_COUNT[pid],
            'statement': {'path': str((root / f'statements/{pid}.md').resolve()), 'sha256': oracle.STATEMENT_SHA256[pid]},
            'domain_validator': DOMAIN, 'comparison_policy': 'exact',
            'source_interface': 'commonjs-function-solve-v1' if language == 'javascript' else 'global-solve-v1'}


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
        statements[pid] = pinned(args.input_root / f'statements/{pid}.md', oracle.STATEMENT_SHA256[pid])
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
                'effects': 'Read-only arguments; exact typed numeric return; no return-to-input aliases; no external IO.',
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
