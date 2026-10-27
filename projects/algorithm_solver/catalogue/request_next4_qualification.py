"""Freeze the fixed next-four request candidates for the existing imported runner.

Only newly generated public-definition cases are admitted here. Original source
bytes remain separate from new statement snapshots: historical statement byte
identity was not recorded. This module neither executes nor promotes candidates.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from . import imported_qualification as q
from .boundary_policy import authorize_before_open
from .known_spec_service import KnownSpecService, _boundary_snapshot

IDS = (3228, 3523, 3558, 3597)
LANGUAGES = ('javascript', 'python')
DOMAIN = 'request-next4-v1'
MANIFEST_SHA256 = 'ae33e63c7947475febe108a1f871e36cb06592e45b43df3231ccabe6536c496f'
SOURCE_SHA256 = {
    3228: {'javascript': '0e8ad2b50836156f7a3d2714969a1ab5ab6e5382c0ec4e1aa67f4cdc49df49a9',
           'python': '118a8dd9f4a5ceeb7975d38f16474c42d979436c9526faa261e9e2bf760f5846'},
    3523: {'javascript': '32f3e0f1b6cb72a38fe225be1dece347c08dcabff1bcee3203fe79c872d218e2',
           'python': '9ddaa1002c12de27914133b90ca81c55d3c62b589fef7c26bb6744af4ef0a865'},
    3558: {'javascript': 'd749291734edf67e7eabf4b3b4777237edea54d49907acd06b6060728912ae5e',
           'python': '8d755b4ff604c89e5aebd9d8711f00362e69d15eeac41541d8d6bec3700ccdce'},
    3597: {'javascript': '6fdf167796e4490af694c7bdbcfc867defc86f111a6beb11866c24a1e0f0b26c',
           'python': '09b142e7c9f8ef047b8f4fe0205270eb490a5afa5255685df80399dd3898495f'},
}
PROVENANCE_SHA256 = {
    3228: '6a012515277233b32726b897511da50a7c2389f116abd91e7f6e689181d33dc0',
    3523: '8e516ef6df6d56681013c11e9404ca12caf6601cd633fb5049ebce2a33ba5570',
    3558: '9663b5c58fec3a215db1ad1505d934019fffce9e4ef695e4820ec2539e8f152e',
    3597: '05f51f7bee6fbe88f7f7c70cd98aa4610280a3203a67841c6ce19906dbcda4da',
}


def validate(pid, args):
    from . import request_next4_oracles as oracle
    oracle.validate(pid, args)


def read_manifest(path):
    raw = q.read(path)
    if q.sha(raw) != MANIFEST_SHA256:
        raise ValueError('original request manifest changed')
    rows = [row for row in q.decode(raw) if row.get('problem_id') in IDS]
    if len(rows) != len(IDS) or {row['problem_id'] for row in rows} != set(IDS):
        raise ValueError('fixed target missing or duplicated in original manifest')
    selected = {row['problem_id']: row for row in rows}
    for pid, row in selected.items():
        for language, suffix in (('javascript', 'js'), ('python', 'py')):
            if row['source_files'][language] != {'path': f'{language}/{pid}.{suffix}',
                                                'sha256': SOURCE_SHA256[pid][language]}:
                raise ValueError('original manifest exact source binding differs')
    return selected


def additional_code():
    return {str(Path(module).resolve()): q.file_hash(module)
            for module in (__file__, Path(__file__).with_name('request_next4_oracles.py'))}


def definition_provenance(path, pid):
    from . import request_next4_oracles as oracle
    raw = q.read(path, 131072)
    if q.sha(raw) != PROVENANCE_SHA256[pid]:
        raise ValueError('new definition provenance drift')
    value = q.decode(raw)
    if (value.get('problem_id') != pid or value.get('original_manifest_sha256') != MANIFEST_SHA256 or
            value.get('new_statement_prefix_sha256') != oracle.STATEMENT_SHA256[pid] or
            value.get('original_statement_equivalence_established') is not False or
            value.get('original_statement_byte_pin_present') is not False):
        raise ValueError('new definition provenance identity differs')
    return raw


def generated(pid, statement):
    from . import request_next4_oracles as oracle
    if q.sha(statement) != oracle.STATEMENT_SHA256[pid]:
        raise ValueError('new statement snapshot drift')
    cases, categories = oracle.build_cases(pid, statement)
    if (len(cases) != oracle.CASE_COUNT[pid] or q.sha(q.encoded(cases)) != oracle.CASES_SHA256[pid] or
            not isinstance(categories, list) or len(categories) != len(cases) or
            any(not isinstance(category, str) or not category for category in categories)):
        raise ValueError('hard-pinned generated cases or categories differ')
    for case in cases:
        oracle.validate(pid, case['args'])
    groups = list(q.batches(cases))  # Oversized cases fail; none are dropped.
    design = {'case_count': len(cases), 'tests_raw_sha256': oracle.CASES_SHA256[pid],
              'batch_count_per_language': len(groups),
              'largest_packet_bytes': max(len(q.encoded(q.packet(batch))) for _, batch in groups)}
    provenance = {'categories': categories, 'counts': dict(Counter(categories)),
                  'statement_provenance_sha256': PROVENANCE_SHA256[pid]}
    return cases, design, provenance


def pre_source_record(designs):
    from . import request_next4_oracles as oracle
    return {'schema': 'gamma.request-next4-pre-source-freeze.v1', 'problem_ids': list(IDS),
            'source_payload_reads_at_freeze': 0,
            'read_count_scope': 'This preparation command only; later preparation does not restore global blindness or freshness.',
            'original_statement_byte_equivalence': False, 'manifest_sha256': MANIFEST_SHA256,
            'statement_sha256': {str(pid): oracle.STATEMENT_SHA256[pid] for pid in IDS},
            'statement_provenance_sha256': {str(pid): PROVENANCE_SHA256[pid] for pid in IDS},
            'expected_source_sha256': {str(pid): SOURCE_SHA256[pid] for pid in IDS},
            'generated_cases': designs, 'additional_code': additional_code(), 'observer_code': q.code_pins(),
            'limits': q.LIMITS, 'max_packet_bytes': q.MAX_PACKET}


def verify_freeze(root, contract, gate):
    """Check fixed IDs/interfaces before payloads, then all retained evidence pins."""
    jobs = contract.get('jobs', [])
    if (contract.get('schema') != 'gamma.imported-independent-execution.v1' or
            contract.get('selected_problem_ids') != list(IDS) or
            contract.get('pending') != [] or contract.get('automatic_promotion') is not False or
            contract.get('protected_access') is not False or
            contract.get('original_statement_byte_equivalence') is not False or
            contract.get('limits') != q.LIMITS or contract.get('max_packet_bytes') != q.MAX_PACKET or
            contract.get('code') != q.code_pins() or
            [(job.get('id'), job.get('language')) for job in jobs] != [(pid, lang) for pid in IDS for lang in LANGUAGES] or
            contract.get('additional_code') != additional_code()):
        raise ValueError('fixed eight-job population or module pins differ')
    from . import request_next4_oracles as oracle
    for job in jobs:
        pid, language = job['id'], job['language']; suffix = 'js' if language == 'javascript' else 'py'
        expected_interface = 'commonjs-object-solve-v1' if language == 'javascript' else 'global-solve-v1'
        if (set(job) != {'id', 'language', 'source', 'source_sha256', 'original_source', 'tests',
                         'tests_raw_sha256', 'tests_canonical_sha256', 'case_count', 'statement',
                         'domain_validator', 'comparison_policy', 'source_interface'} or
                job['source'] != f'sources/{pid}.{suffix}' or job['tests'] != f'tests/{pid}.json' or
                job['source_sha256'] != SOURCE_SHA256[pid][language] or
                job['statement'] != {'path': str((root / f'statements/{pid}.md').resolve()),
                                     'sha256': oracle.STATEMENT_SHA256[pid]} or
                job['domain_validator'] != DOMAIN or job['comparison_policy'] != 'exact' or
                q.source_interface(job) != expected_interface or job['case_count'] != oracle.CASE_COUNT[pid] or
                job['tests_raw_sha256'] != oracle.CASES_SHA256[pid]):
            raise ValueError('fixed source/domain/interface evidence differs')
    for pid in IDS:
        for language in LANGUAGES:
            authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'], language=language)
    pre_raw = q.read(root / 'pre-source-freeze.json')
    provenance_raw = q.read(root / 'case-provenance.json')
    if (q.sha(pre_raw) != contract.get('pre_source_freeze_sha256') or
            q.sha(provenance_raw) != contract.get('case_provenance_sha256')):
        raise ValueError('pre-source or case provenance artifact drift')
    pre, provenance = q.decode(pre_raw), q.decode(provenance_raw)
    if pre != pre_source_record(pre.get('generated_cases')):
        raise ValueError('pre-source evidence binding differs')
    read_manifest(root / 'original-manifest.json')
    designs, expected_provenance = {}, {}
    for pid in IDS:
        definition_provenance(root / f'statements/{pid}.provenance.json', pid)
        authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'],
                              language='python', payload_kind='statement')
        cases, design, origin = generated(pid, q.read(root / f'statements/{pid}.md', 131072))
        raw = q.read(root / f'tests/{pid}.json')
        if raw != q.encoded(cases) or any(job['tests_canonical_sha256'] != q.canonical_tests_hash(cases)
                                        for job in jobs if job['id'] == pid):
            raise ValueError('frozen generated cases drift')
        designs[str(pid)], expected_provenance[str(pid)] = design, origin
    if designs != pre['generated_cases'] or provenance != expected_provenance:
        raise ValueError('generated case design provenance differs')


def prepare(args):
    runtime_identity = q.runtime(getattr(args, 'node_runtime', None))
    KnownSpecService.from_config(args.config, args.config_sha256)
    config = q.decode(q.read(args.config))
    gate = q.decode(q.read(config['source_access']['boundary_gate']['path']))
    if not {f'leetcode:{pid}' for pid in IDS} <= _boundary_snapshot(gate).authorized:
        raise PermissionError('fixed request population is not currently authorized')
    for pid in IDS:
        for language in LANGUAGES:
            authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'], language=language)
    rows = read_manifest(args.manifest)
    sources = {(pid, lang): args.source_root / rows[pid]['source_files'][lang]['path']
               for pid in IDS for lang in LANGUAGES}
    if any(path.is_symlink() or not path.is_file() for path in sources.values()):
        raise ValueError('all eight exact source locators must exist before payload access')
    from . import request_next4_oracles as oracle
    statements, origins, all_cases, designs, provenance = {}, {}, {}, {}, {}
    for pid in IDS:
        origins[pid] = definition_provenance(args.statement_root / str(pid) / 'provenance.json', pid)
        authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'],
                              language='python', payload_kind='statement')
        statements[pid] = q.read(args.statement_root / str(pid) / 'statement.tool-prefix.txt', 131072)
        cases, design, origin = generated(pid, statements[pid])
        all_cases[pid], designs[str(pid)], provenance[str(pid)] = cases, design, origin
    manifest_raw = q.read(args.manifest)
    if q.sha(manifest_raw) != MANIFEST_SHA256:
        raise ValueError('original manifest changed during preparation')
    args.output.mkdir(parents=True, exist_ok=False)
    for directory in ('sources', 'tests', 'statements'):
        (args.output / directory).mkdir()
    (args.output / 'original-manifest.json').write_bytes(manifest_raw)
    for pid in IDS:
        q.write(args.output / f'tests/{pid}.json', all_cases[pid])
        (args.output / f'statements/{pid}.md').write_bytes(statements[pid])
        (args.output / f'statements/{pid}.provenance.json').write_bytes(origins[pid])
    q.write(args.output / 'case-provenance.json', provenance)
    q.write(args.output / 'pre-source-freeze.json', pre_source_record(designs))
    jobs = []
    for pid in IDS:
        for language, suffix in (('javascript', 'js'), ('python', 'py')):
            authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'], language=language)
            raw = q.read(sources[(pid, language)], 1024 * 1024)
            if q.sha(raw) != SOURCE_SHA256[pid][language]:
                raise ValueError('original candidate bytes differ; no replacement authorized')
            source = f'sources/{pid}.{suffix}'
            (args.output / source).write_bytes(raw)
            cases = all_cases[pid]
            jobs.append({'id': pid, 'language': language, 'source': source, 'source_sha256': q.sha(raw),
                'original_source': str(sources[(pid, language)].resolve()), 'tests': f'tests/{pid}.json',
                'tests_raw_sha256': oracle.CASES_SHA256[pid], 'tests_canonical_sha256': q.canonical_tests_hash(cases),
                'case_count': len(cases), 'statement': {'path': str((args.output / f'statements/{pid}.md').resolve()),
                    'sha256': oracle.STATEMENT_SHA256[pid]}, 'domain_validator': DOMAIN, 'comparison_policy': 'exact',
                'source_interface': 'commonjs-object-solve-v1' if language == 'javascript' else 'global-solve-v1'})
    contract = {'schema': 'gamma.imported-independent-execution.v1', 'jobs': jobs, 'pending': [],
        'service_config': str(args.config.resolve()), 'service_config_sha256': args.config_sha256,
        'runtime': runtime_identity, 'code': q.code_pins(), 'limits': q.LIMITS, 'additional_code': additional_code(),
        'max_packet_bytes': q.MAX_PACKET, 'selected_problem_ids': list(IDS),
        'pre_source_freeze_sha256': q.file_hash(args.output / 'pre-source-freeze.json'),
        'case_provenance_sha256': q.file_hash(args.output / 'case-provenance.json'),
        'test_authority': 'Owner-authorized bounded independent qualification using new public-definition cases, not acquired historical/private cases.',
        'effects': 'Read-only arguments; exact typed scalar or fresh ordered string-list return, no return-to-input alias.',
        'comparison': 'Exact typed returns and local effects against independent public-definition oracles.',
        'scope': 'Finite in-domain development checks; not universal proof, fresh heldout confirmation, full-domain performance qualification or catalogue adoption.',
        'original_statement_byte_equivalence': False, 'automatic_promotion': False, 'protected_access': False}
    q.write(args.output / 'contract.json', contract)
    return {'jobs': len(jobs), 'cases_per_language_by_id': {str(pid): len(all_cases[pid]) for pid in IDS},
            'checks': 2 * sum(len(cases) for cases in all_cases.values()),
            'batches_per_language_by_id': {pid: row['batch_count_per_language'] for pid, row in designs.items()},
            'contract_sha256': q.file_hash(args.output / 'contract.json')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'manifest', 'statement-root', 'source-root', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--node-runtime', type=Path)
    print(q.encoded(prepare(parser.parse_args())).decode(), end='')
