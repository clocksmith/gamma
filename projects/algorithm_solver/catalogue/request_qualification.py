"""Prepare a fixed, independently reviewable request-252 problem 3215 pilot.

This is a case/domain and freeze owner, not a new execution engine or registry.
The imported qualification runner executes both languages and its separate
verifier replays observations. No historical or private cases are acquired.
Later problems require their own definition, oracle and interface review.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import html
from itertools import product
from pathlib import Path
import random
import re

from . import imported_qualification as q
from .boundary_policy import authorize_before_open
from .known_spec_service import KnownSpecService, _boundary_snapshot

PID = 3215
IDENTITY = 'leetcode:3215'
SEED = 202610273215
CASE_COUNT = 815
CASES_SHA256 = 'bb344a98f00ea415d1e5a9644d712c8b7c3b13010548b1cba66951ee7ffb072a'
MANIFEST_SHA256 = 'ae33e63c7947475febe108a1f871e36cb06592e45b43df3231ccabe6536c496f'
STATEMENT_SHA256 = '930c2e12cefeea550d26f5b9c1ae3e56fa7830fd6f36d4e13c02a6ca2a36a3ff'
SOURCE_SHA256 = {
    'javascript': '6dae4ca4cc55e3450a1bc6bb307124fb0c54d4985710d6dc8cb09f38ecd3efa3',
    'python': '6e107be508da7e3aea2c4ac92bcf3be469860be31ac34ad2d462ed2bf630547f',
}
ORACLE_PREDECESSOR = {
    'path': 'projects/algorithm_solver/catalogue/authored/request-252-v1/batch1/test_candidates.py',
    'git_blob': '8daeca7b095b194bd73803de187a6077b3874fd1',
    'sha256': 'f22d02d46482a1b27ed8fe8bf7693d3939278f4a60b36ebdf0ea3566a2c106b7',
    'mechanism': 'Direct Cartesian XOR-popcount enumeration; not cross-language agreement.',
}


def validate(pid, args):
    if (type(pid) is not int or pid != PID or type(args) is not list or len(args) != 3 or
            any(type(values) is not list or not 1 <= len(values) <= 100000 or
                any(type(value) is not int or not 0 <= value <= 10**9 for value in values)
                for values in args)):
        raise ValueError('3215: outside pinned three-array integer domain')


def expected(args):
    """Existing batch oracle mechanism, bounded before enumeration."""
    validate(PID, args)
    if len(args[0]) * len(args[1]) * len(args[2]) > 100000:
        raise ValueError('enumeration budget exceeded; use separately justified analytic fixtures')
    return sum((a ^ b ^ c).bit_count() % 2 == 0 for a, b, c in product(*args))


def public_examples(raw):
    if q.sha(raw) != STATEMENT_SHA256:
        raise ValueError('exact statement prefix changed')
    text = html.unescape(re.sub('<[^>]*>', '', raw.decode('utf-8')))
    cases = []
    for match in re.finditer(r'Input:\s*(.*?)\s*Output:\s*(\d+)\s*Explanation:', text, re.S):
        call = ast.parse('f(' + match[1].strip() + ')', mode='eval').body
        if (not isinstance(call, ast.Call) or call.args or
                [item.arg for item in call.keywords] != ['a', 'b', 'c']):
            raise ValueError('pinned example ordered arguments differ')
        args = [ast.literal_eval(item.value) for item in call.keywords]
        answer = int(match[2])
        if expected(args) != answer:
            raise ValueError('independent oracle disagrees with pinned example')
        cases.append({'args': args, 'expected': answer, 'compare': 'return'})
    if len(cases) != 2:
        raise ValueError('both pinned public examples are required')
    return cases


def build_cases(statement):
    """Generate only this permitted development pilot, before candidate reads."""
    cases = public_examples(statement)
    categories = ['pinned_public_example'] * len(cases)

    def add(args, category, answer=None):
        validate(PID, args)
        answer = expected(args) if answer is None else answer
        if type(answer) is not int or not 0 <= answer <= len(args[0]) * len(args[1]) * len(args[2]):
            raise ValueError('invalid independently specified count')
        cases.append({'args': args, 'expected': answer, 'compare': 'return'})
        categories.append(category)

    for values in product(range(8), repeat=3):
        add([[value] for value in values], 'exhaustive_small_singletons')
    rng = random.Random(SEED)
    for _ in range(80):
        add([[rng.randrange(32) for _ in range(rng.randrange(1, 7))] for _ in range(3)],
            'seeded_small_cartesian_oracle')
    high = (0, 1, 2**29, 2**29 + 1, 10**9 - 1, 10**9)
    for values in product(high, repeat=3):
        add([[value] for value in values], 'high_bit_cartesian_oracle')
    # Analytic shape/numeric probes are distinct from enumerated expectations.
    # 0 XOR 0 XOR 0 has even parity for every positional choice.
    add([[0] * 100000 for _ in range(3)], 'analytic_maximum_count', 10**15)
    # Every choice has exactly one set bit.
    add([[1] * 100000, [0] * 100000, [0] * 100000], 'analytic_maximum_shape_odd', 0)
    # Each array has one odd-parity high bit: zero or two chosen high bits pass.
    add([[2**29] + [0] * 99999 for _ in range(3)], 'analytic_sparse_high_bit_maximum_shape',
        99999**3 + 3 * 99999)
    # Equal high values cancel before XOR with zero, independently of bit width.
    add([[10**9] * 100, [10**9] * 100, [0] * 100], 'analytic_dense_high_bit', 100**3)
    add([[0, 2**29] * 50000, [2**29], [0]], 'analytic_unbalanced_high_bit_shape', 50000)
    if len(cases) != CASE_COUNT or q.sha(q.encoded(cases)) != CASES_SHA256:
        raise ValueError('frozen generated-case population or bytes changed')
    return cases, categories


def read_manifest(path):
    raw = q.read(path)
    if q.sha(raw) != MANIFEST_SHA256:
        raise ValueError('original request manifest changed')
    rows = [row for row in q.decode(raw) if row.get('problem_id') == PID]
    if len(rows) != 1:
        raise ValueError('fixed target missing or duplicated in manifest')
    row = rows[0]
    if row['definition_provenance']['definition_prefix_sha256'] != STATEMENT_SHA256:
        raise ValueError('manifest statement binding differs')
    for language, suffix in (('javascript', 'js'), ('python', 'py')):
        if row['source_files'][language] != {'path': f'{language}/{PID}.{suffix}', 'sha256': SOURCE_SHA256[language]}:
            raise ValueError('manifest exact source binding differs')
    return row


def verify_freeze(root, contract, gate):
    """Check all pilot evidence pins during execution and independent replay."""
    if (contract.get('selected_problem_ids') != [PID] or
            [(j.get('id'), j.get('language')) for j in contract['jobs']] != [(PID, 'javascript'), (PID, 'python')]):
        raise ValueError('fixed dual-language request population differs')
    pre_raw = q.read(root / 'pre-source-freeze.json')
    provenance_raw = q.read(root / 'case-provenance.json')
    if (q.sha(pre_raw) != contract.get('pre_source_freeze_sha256') or
            q.sha(provenance_raw) != contract.get('case_provenance_sha256')):
        raise ValueError('pre-source or case provenance artifact drift')
    pre, provenance = q.decode(pre_raw), q.decode(provenance_raw)
    if (pre.get('schema') != 'gamma.request3215-pre-source-freeze.v1' or pre.get('problem_ids') != [PID] or
            pre.get('source_payload_reads_at_freeze') != 0 or pre.get('manifest_sha256') != MANIFEST_SHA256 or
            pre.get('statement_sha256') != STATEMENT_SHA256 or
            pre.get('cases_per_language') != CASE_COUNT or pre.get('tests_raw_sha256') != CASES_SHA256 or
            pre.get('generator_validator_sha256') != q.file_hash(__file__) or
            pre.get('observer_code') != q.code_pins() or pre.get('expected_source_sha256') != SOURCE_SHA256 or
            pre.get('limits') != q.LIMITS or pre.get('max_packet_bytes') != q.MAX_PACKET):
        raise ValueError('pre-source evidence binding differs')
    if (provenance.get('seed') != SEED or provenance.get('predecessor') != ORACLE_PREDECESSOR or
            type(provenance.get('categories')) is not list or
            len(provenance['categories']) != pre.get('cases_per_language') or
            provenance.get('counts') != dict(Counter(provenance['categories']))):
        raise ValueError('case design provenance differs')
    statement = {'path': str((root / 'statement.md').resolve()), 'sha256': STATEMENT_SHA256}
    for job in contract['jobs']:
        expected_interface = 'commonjs-object-solve-v1' if job['language'] == 'javascript' else 'global-solve-v1'
        if (job.get('statement') != statement or job.get('domain_validator') != 'request3215-v1' or
                job.get('source_interface') != expected_interface or job.get('comparison_policy') != 'exact' or
                job.get('source_sha256') != SOURCE_SHA256[job['language']] or
                job.get('case_count') != pre['cases_per_language'] or
                job.get('tests_raw_sha256') != pre['tests_raw_sha256']):
            raise ValueError('job differs from fixed source/domain/interface evidence')
    authorize_before_open(IDENTITY, gate['artifact_paths'], gate['trusted_hashes'], language='python', payload_kind='statement')
    if q.sha(q.read(root / 'statement.md', 131072)) != STATEMENT_SHA256:
        raise ValueError('frozen statement drift')


def prepare(args):
    runtime_identity = q.runtime(getattr(args, 'node_runtime', None))
    KnownSpecService.from_config(args.config, args.config_sha256)
    config = q.decode(q.read(args.config))
    gate = q.decode(q.read(config['source_access']['boundary_gate']['path']))
    boundary = _boundary_snapshot(gate)
    if IDENTITY not in boundary.authorized:
        raise PermissionError('fixed request target is not currently authorized')
    # Complete both languages' metadata checks before any statement/source read.
    for language in SOURCE_SHA256:
        authorize_before_open(IDENTITY, gate['artifact_paths'], gate['trusted_hashes'], language=language)
    row = read_manifest(args.manifest)
    sources = {language: args.source_root / item['path'] for language, item in row['source_files'].items()}
    if any(path.is_symlink() or not path.is_file() for path in sources.values()):
        raise ValueError('both exact source locators must exist before payload access')
    authorize_before_open(IDENTITY, gate['artifact_paths'], gate['trusted_hashes'], language='python', payload_kind='statement')
    statement = q.read(args.statement, 131072)
    cases, categories = build_cases(statement)
    groups = list(q.batches(cases))  # No oversized input may be silently dropped.
    args.output.mkdir(parents=True, exist_ok=False)
    for directory in ('sources', 'tests'):
        (args.output / directory).mkdir()
    tests = f'tests/{PID}.json'
    q.write(args.output / tests, cases)
    (args.output / 'statement.md').write_bytes(statement)
    q.write(args.output / 'case-provenance.json', {'seed': SEED, 'categories': categories,
                                                 'counts': dict(Counter(categories)), 'predecessor': ORACLE_PREDECESSOR})
    # This record exists before the first candidate byte is read. Failed source
    # binding checks leave it intact; the command never replaces existing runs.
    pre_source = {'schema': 'gamma.request3215-pre-source-freeze.v1', 'problem_ids': [PID],
                  'source_payload_reads_at_freeze': 0, 'cases_per_language': len(cases),
                  'tests_raw_sha256': q.file_hash(args.output / tests),
                  'statement_sha256': STATEMENT_SHA256, 'manifest_sha256': MANIFEST_SHA256,
                  'generator_validator_sha256': q.file_hash(__file__), 'observer_code': q.code_pins(),
                  'expected_source_sha256': SOURCE_SHA256, 'limits': q.LIMITS,
                  'max_packet_bytes': q.MAX_PACKET, 'batch_count_per_language': len(groups),
                  'largest_packet_bytes': max(len(q.encoded(q.packet(batch))) for _, batch in groups)}
    q.write(args.output / 'pre-source-freeze.json', pre_source)
    jobs = []
    for language, suffix in (('javascript', 'js'), ('python', 'py')):
        authorize_before_open(IDENTITY, gate['artifact_paths'], gate['trusted_hashes'], language=language)
        raw = q.read(sources[language], 1024 * 1024)
        if q.sha(raw) != SOURCE_SHA256[language]:
            raise ValueError('original candidate bytes differ; no replacement authorized')
        source = f'sources/{PID}.{suffix}'
        (args.output / source).write_bytes(raw)
        jobs.append({'id': PID, 'language': language, 'source': source, 'source_sha256': q.sha(raw),
                     'original_source': str(sources[language].resolve()), 'tests': tests,
                     'tests_raw_sha256': pre_source['tests_raw_sha256'],
                     'tests_canonical_sha256': q.canonical_tests_hash(cases), 'case_count': len(cases),
                     'statement': {'path': str((args.output / 'statement.md').resolve()), 'sha256': STATEMENT_SHA256},
                     'domain_validator': 'request3215-v1', 'comparison_policy': 'exact',
                     'source_interface': 'commonjs-object-solve-v1' if language == 'javascript' else 'global-solve-v1'})
    contract = {'schema': 'gamma.imported-independent-execution.v1', 'jobs': jobs, 'pending': [],
                'service_config': str(args.config.resolve()), 'service_config_sha256': args.config_sha256,
                'runtime': runtime_identity, 'code': q.code_pins(), 'limits': q.LIMITS,
                'additional_code': {str(Path(__file__).resolve()): q.file_hash(__file__)},
                'max_packet_bytes': q.MAX_PACKET, 'selected_problem_ids': [PID],
                'pre_source_freeze_sha256': q.file_hash(args.output / 'pre-source-freeze.json'),
                'case_provenance_sha256': q.file_hash(args.output / 'case-provenance.json'),
                'test_authority': 'Owner-authorized bounded independent qualification; newly generated public-definition Cartesian and analytic cases, not acquired historical/private cases.',
                'effects': 'Read-only three-array arguments; scalar integer return, no return-to-input alias.',
                'comparison': 'Exact Python int / JavaScript Number return and local effects.',
                'scope': 'Finite in-domain development checks; not universal proof, fresh heldout confirmation, full-domain performance qualification or catalogue adoption.',
                'automatic_promotion': False, 'protected_access': False}
    q.write(args.output / 'contract.json', contract)
    return {'jobs': len(jobs), 'cases_per_language': len(cases), 'checks': len(cases) * len(jobs),
            'batches_per_language': len(groups), 'contract_sha256': q.file_hash(args.output / 'contract.json')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'manifest', 'statement', 'source-root', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--node-runtime', type=Path)
    print(q.encoded(prepare(parser.parse_args())).decode(), end='')
