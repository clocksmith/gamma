"""Freeze ten exact D/E candidates through the existing imported runner.

Original source-blind chronology, reviewed original bytes, deterministic cases,
and batch grouping remain pinned. No candidate execution or promotion occurs.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from . import imported_qualification as q
from .boundary_policy import authorize_before_open
from .known_spec_service import KnownSpecService, _boundary_snapshot

IDS = (3513, 3522, 3527, 3546, 3572, 3227, 3234, 3556, 3577, 3584)
LANGUAGES = ('javascript', 'python')
DOMAIN = 'request-parallel10-v1'
MANIFEST_SHA256 = {4: '9ac23ea2791681944fb6dcd0e010cb8cde996cde7fca1f9091d70645e8330eec'}
MANIFEST_BATCH = {3513: 4, 3522: 4, 3527: 4, 3546: 4, 3572: 4, 3227: 4, 3234: 4, 3556: 4, 3577: 4, 3584: 4}
SOURCE_SHA256 = {3513: {'javascript': '54e95372d6a52b6264caaa316f50d67123adaa78a6bcd514319dec02aad66fe9',
        'python': '86f6dfcca4e0efa3cfde91a4c8be5a8c6c5e2eb7e44a62a992889358dd96107a'},
 3522: {'javascript': '8695908f9ce70f04bbafa6038d686dc2ecb7f429217df7290b6b021bb512ad04',
        'python': '09c49617e5d3ae1c9faf0f0bf86ed2bbfa763da714eab0bd5918d88a17f29207'},
 3527: {'javascript': '1109f22aa0601b29f58a14b897bd0d1c32285440a20df453bee281329c2869e4',
        'python': 'f2e8357304283fbc856d587279faa370450af28351d68cbd01aabb7ec97d3b15'},
 3546: {'javascript': '6556e75325356c971d0037ed52e3fbb1ff089022b9f6caa64a9f448695b2079f',
        'python': '51cb6bd47a4e3f761627a23b397ad786c04c3c133b67b341e72e9df1a400dc42'},
 3572: {'javascript': '9416fa8ebc90987025b1bf7f7ada8c900d66c70b2b410f8922a2be00c7ba14f5',
        'python': 'c566baf277aafbf9251b7159c8957e6c0020abd8fb927bef18f03fdd35aafd14'},
 3227: {'javascript': '63c232103b91dea26ba4cca35609e16041db27257e727b4a766e37d22ff3ccb1',
        'python': '705ae7427ae375b0ab4c50c8cc2b4110b6e3ecef2c4fad467f31920f0c2425dc'},
 3234: {'javascript': '16b4e59024d23c5cae761e4d776cc955ad3efd33d90bbf2bdbc572e8c1a79896',
        'python': '64ed767b256c23663524187b7608c3c7105acd271378e3d2bbd77f6c38af8961'},
 3556: {'javascript': '4e599b7f92fc531cb8be072b5328533763f01cb63a3f5cd19c74ed904b13f912',
        'python': '97e793438092729e746d2ee1114e4c13bf698e30a1442bc412291b6cb39c5e2a'},
 3577: {'javascript': 'e6335dde001573d3fe27b1814cea9100cc917bfd90384e91de9c2ab2abc1d89b',
        'python': '9581b1ec4d9550c733a37700ae76bcebae0cae849041e192aa80571a84169ca0'},
 3584: {'javascript': '3d2db31c170b398823ac06283fafe46068a1e41d7f91673bf851ee7e5d0b79dd',
        'python': 'f11116c2c07039e80eaf80dbb773650bfe464b2fb8e034c10c0c1ed24e3d8a51'}}
PROVENANCE_SHA256 = {3513: '778abf9bf26ef3d567fb2c2c09dc90fcc9ce134aef6ec81eb03577c8edc33ed9',
 3522: '42e6514e25b4b4ef6caf9a50879f690fecbe9f0c50469fabb354bbfe7cc8029a',
 3527: 'e8e24ddef559b9ca5b4f3206fe2bcbba1af967a084e6f7b5946130c36bb9dcb2',
 3546: 'c4540a4196a3855178f7ee8191ec94503c36be71676cf9512be0eedbec300bd6',
 3572: '4b321fa6cdf29672a233fb63a899da606fab356f12685a506bffa57d7d721ff5',
 3227: '0c1f54c5a3f4a8694bf5a16a848d2b7bac4551bcce387ac595dc7dfb68b0bb92',
 3234: 'c243e009b51b791e310caa37857f046d5c8bb6edab2c52dc9e9bd47a888d5df6',
 3556: '6e988c7c8fabc45708e7d4a4b5ec48b71f0eb6064dcbe5e248a03ec5af6e934d',
 3577: 'ef2aba7bcf22d4884f7da4d43b03aa17981e3d055e282a570045b1d78637318b',
 3584: '3bcd6d45ea2683cac60b985b672c36e0af1bb944c7f2d416606a667eb77637e4'}
CATEGORIES_SHA256 = {3513: '7c28b35396df1f479d4e7e5915afa1269e2d1a2ebe26e58facc75520a5ad7135',
 3522: '8e3f4d42c6dbffe5de3ae6d7596ffece5571f21b53d6f84882c07c6776458da2',
 3527: '635ea84f4a40c87c48c05a3ba18b768418ffd340f14b35a7de924e8cbc900565',
 3546: '0d2d9b776fd388d0f60145a814ebb32a82ce09bc1a58db219dd76f5f8f239755',
 3572: '398db81b5873763fe18ea0597faec22e3456596452c7bc10ce9713201789e88d',
 3227: 'cddab11764fed4e823bf5362a1bb8772b627271a2c427c5dedb85d3e26004719',
 3234: '3ea6df9c20cc48610405c765cfce9b7455702ffac59b810a23b10cc0d21affe9',
 3556: 'fc621de2cd74d3146d7ee9daa7feabf4e92dd240d62238bf5cec204a19491903',
 3577: '760cda0fbfe39fcbcf0bec49640f3adfdf9f4928d2686cf7d2307fd21eb9436a',
 3584: '8905cc02ddb12e86285f0184527a9125408207d14d83d310f9f57657127e8ba5'}
BATCHES_SHA256 = {3513: '65e1492cf325c26b1d4636b131ce73f93af407c41626500383ef7a2fe2be0b20',
 3522: 'df0388e7ab3d038172972fbfe5926064e148a9309c1531bdd13bdc7f56fe2d08',
 3527: '9c8158b464ab7b591ba5e6dd760a56004953e6aa6ed7d4ce1f7eba144eed041a',
 3546: 'd4e4e1417c69448342d1f75d14c2e2707f7a05fb69b42ad08dcbf795f747cd05',
 3572: 'a50b9505755466f7cf776d69d67f171024fde89025bd9bf4a12d8e650b57ab8c',
 3227: 'c45b05d0739caa85ea9a2109d0991c183336b20caa1b4846272947d8d59a65d7',
 3234: 'b81db8e1469b449718696253f4a2c2c3f2dae90bac2d3be8ca2028fc93be6715',
 3556: '6ddb0c89b2480d59f7935fc57363819eeaa976df0667a741d7a90615b2d6d2e4',
 3577: '19ed806125215c5b9e57b42196d6151125d824a935c8dcebe71195143522f847',
 3584: '7eeef12d0f3cd27dfd208d92129b7adfd20521a80973ca9cdac6670a3b26a418'}
ORIGINAL_EVIDENCE = {'d': {'original-freeze.json': 'd695fddf0154bc2c3e28a2a39b3696473feeb13e6056f55ba831cf1da8030e60',
       'independent-review.json': '0d08b8b10994fe314fd3c9f4e126ea270a5a25388c0e1e51c32378332912b5b7',
       'source-acquisition.json': '7998525f6c0acaf9aaba48b508e0519440538fb427a36dbb2763ec02557c2305',
       'first-static-review.json': 'e4e4fc053c13e314c86e8ea95ac1250c2e8625e05a749353b774e5efa0b5a31a',
       'second-static-review.json': '24742e929d376856ac7c3992577c23e6b54630028e3b4c562cc943b387f9cc89'},
 'e': {'original-freeze.json': '7508631030cdaf090839973ca12ac889f9e2aaebe18679200c95b21fa8a2e7f4',
       'independent-review.json': 'e59ae9c51f41c7db4009a71415b3215b6793abb1538b9a07579d37676af242e4',
       'source-acquisition.json': '37d7b22199d25924a8ac9d3c01f9394fdc45f66c118edf3e4f20925df1f16d77',
       'first-static-review.json': '2e52805d9c637829427c5663c313b1ad6557f6a26e7db7219c6b7634aee61964',
       'second-static-review.json': '0238e6c201921a071820166081fde8734323aa718c61eebd7f41212b1d58f0b5'}}
DEFINITION_INDEX_SHA256 = {'d': '39fe372776d3c5d5383014ebf76ebf98a02e2f028dbfed1ff142afe353816e06',
 'e': 'ffd3e7dd301147fd3f7cef4481b8dd791f6a1fa2517725b45aae6912d47eb12e'}
PREDECESSOR_OBSERVER_SHA256 = '179342c85db7ce35270b7796e1fa27c555f765c6624ed842e9222508c5842629'

def oracle_for(pid):
    if type(pid) is not int or pid not in IDS:
        raise ValueError('problem outside the fixed ten-ID lane')
    from . import request_parallel_d_oracles as d
    from . import request_parallel_e_oracles as e
    return d if pid in IDS[:5] else e


def validate(pid, args):
    oracle_for(pid).validate(pid, args)


def read_manifest(path, batch):
    raw = q.read(path)
    if batch not in MANIFEST_SHA256 or q.sha(raw) != MANIFEST_SHA256[batch]:
        raise ValueError('original batch-specific request manifest changed')
    expected = {pid for pid in IDS if MANIFEST_BATCH[pid] == batch}
    rows = [row for row in q.decode(raw) if row.get('problem_id') in IDS]
    if len(rows) != len(expected) or {row['problem_id'] for row in rows} != expected:
        raise ValueError('fixed target missing, duplicated or in the wrong manifest batch')
    selected = {row['problem_id']: row for row in rows}
    for pid, row in selected.items():
        for language, suffix in (('javascript', 'js'), ('python', 'py')):
            if row['source_files'][language] != {'path': f'{language}/{pid}.{suffix}',
                                                'sha256': SOURCE_SHA256[pid][language]}:
                raise ValueError('original manifest exact source binding differs')
    return selected


def additional_code():
    paths = [Path(__file__), *(Path(__file__).with_name(f'request_parallel_{group}_oracles.py')
                               for group in ('d', 'e')),
             Path(__file__).with_name('imported_clean_domains.py')]
    return {str(path.resolve()): q.file_hash(path) for path in paths}


def original_evidence(root):
    """Preserve both original schemas and all pre-read/static chronology unchanged."""
    retained = {}
    raw = q.read(root / 'observer-predecessor.py')
    if q.sha(raw) != PREDECESSOR_OBSERVER_SHA256:
        raise ValueError('archived pre-source observer differs')
    retained['observer-predecessor.py'] = raw
    for offset, group in enumerate(('d', 'e')):
        values = {}
        for name, expected in ORIGINAL_EVIDENCE[group].items():
            raw = q.read(root / group / name)
            if q.sha(raw) != expected:
                raise ValueError('original immutable chronology drift')
            retained[group + '/' + name] = raw
            values[name] = q.decode(raw)
        frozen, reviewed = values['original-freeze.json'], values['independent-review.json']
        ids = IDS[offset * 5:offset * 5 + 5]
        if (reviewed.get('author_freeze', {}).get('sha256') != ORIGINAL_EVIDENCE[group]['original-freeze.json'] or
                frozen.get('problem_ids' if group == 'd' else 'ids') != list(ids) or
                frozen.get('source_payload_reads_for_selected_ids_at_freeze' if group == 'd' else 'source_payload_reads') != 0 or
                reviewed.get('candidate_executions') != 0 or not reviewed.get('reviewer')):
            raise ValueError('original independent approval or source-blind chronology differs')
        oracle = oracle_for(ids[0])
        code = {Path(row['path']).name: row['sha256'] for row in frozen['code']}
        dependencies = {Path(row['path']).name: row['sha256'] for row in frozen['dependencies']}
        if (q.file_hash(oracle.__file__) != code.get(f'request_parallel_{group}_oracles.py') or
                frozen['definition_pins']['sha256'] != DEFINITION_INDEX_SHA256[group] or
                dependencies.get('imported_qualification.py') != PREDECESSOR_OBSERVER_SHA256):
            raise ValueError('original oracle, definition index or observer differs')
        for name, pin in dependencies.items():
            if name != 'imported_qualification.py' and q.file_hash(Path(__file__).with_name(name)) != pin:
                raise ValueError('original frozen helper drift')
        rows = frozen['cases']
        if len(rows) != 5:
            raise ValueError('original group population differs')
        for row, pid in zip(rows, ids):
            batch_pin = row['batch_file']['sha256'] if group == 'd' else row['batches_sha256']
            if (row['problem_id'] != pid or row['cases'] != oracle.CASE_COUNT[pid] or
                    row['cases_sha256'] != oracle.CASES_SHA256[pid] or
                    row['categories_sha256'] != CATEGORIES_SHA256[pid] or batch_pin != BATCHES_SHA256[pid]):
                raise ValueError('original fixed case, category or batch population differs')
        for name in ('source-acquisition.json', 'first-static-review.json', 'second-static-review.json'):
            record = values[name]
            rows = record.get('rows', record.get('reviewed_sources', []))
            if (record.get('candidate_executions') != 0 or
                    [(row.get('problem_id'), row.get('language')) for row in rows] !=
                    [(pid, language) for pid in ids for language in LANGUAGES] or
                    any(row.get('source_sha256') != SOURCE_SHA256[row['problem_id']][row['language']] or
                        row.get('blocking_defects', []) != [] or row.get('blocking_static_defect') is not None
                        for row in rows)):
                raise ValueError('original source acquisition or independent static review differs')
    return retained


def definition_provenance(path, pid):
    oracle = oracle_for(pid)
    raw = q.read(path, 131072)
    if q.sha(raw) != PROVENANCE_SHA256[pid]:
        raise ValueError('new definition provenance drift')
    value = q.decode(raw)
    if value.get('problem_id') != pid:
        raise ValueError('new definition provenance identity differs')
    if pid in IDS[:5]:
        valid = (value.get('statement_prefix', {}).get('sha256') == oracle.STATEMENT_SHA256[pid] and
                 value.get('original_statement_byte_equivalence_claimed') is False and
                 value.get('original_statement_byte_pin') is None and
                 value.get('numeric_heading_checked') is True and value.get('slug_title_checked') is True and
                 value.get('original_manifest_sha256') == MANIFEST_SHA256[4])
    else:
        valid = (value.get('statement_sha256') == oracle.STATEMENT_SHA256[pid] and
                 value.get('original_definition_byte_identity_available') is False and
                 value.get('original_manifest_provenance', {}).get('identity_verified') == pid)
    if not valid:
        raise ValueError('new definition provenance representation differs')
    return raw


def batch_manifest(cases, oracle):
    return [{'offset': offset, 'calls': len(batch),
             'packet_bytes': len(q.encoded(q.packet(batch))),
             'packet_sha256': q.sha(q.encoded(q.packet(batch))),
             'projected_success_stdout_bytes': {language: oracle.expected_observation_bytes(batch, language)
                                                for language in LANGUAGES}}
            for offset, batch in q.batches(cases)]


def generated(pid, statement):
    oracle = oracle_for(pid)
    if q.sha(statement) != oracle.STATEMENT_SHA256[pid]:
        raise ValueError('new statement snapshot drift')
    cases, categories = oracle.build_cases(pid, statement)
    if (len(cases) != oracle.CASE_COUNT[pid] or q.sha(q.encoded(cases)) != oracle.CASES_SHA256[pid] or
            q.sha(q.encoded(categories)) != CATEGORIES_SHA256[pid] or
            not isinstance(categories, list) or len(categories) != len(cases) or
            any(not isinstance(category, str) or not category for category in categories)):
        raise ValueError('hard-pinned generated cases or categories differ')
    for case in cases:
        oracle.validate(pid, case['args'])
    if len(q.encoded(cases)) > q.MAX_FILE:
        raise ValueError('generated case file exceeds unchanged reader cap')
    groups = list(q.batches(cases))  # Oversized cases fail; none are dropped.
    batches = batch_manifest(cases, oracle)
    if q.sha(q.encoded(batches)) != BATCHES_SHA256[pid]:
        raise ValueError('original frozen batch grouping or output projection differs')
    design = {'case_count': len(cases), 'tests_raw_sha256': oracle.CASES_SHA256[pid],
              'batch_count_per_language': len(groups), 'batches_sha256': BATCHES_SHA256[pid],
              'largest_packet_bytes': max(len(q.encoded(q.packet(batch))) for _, batch in groups)}
    provenance = {'categories': categories, 'counts': dict(Counter(categories)),
                  'statement_provenance_sha256': PROVENANCE_SHA256[pid],
                  'original_manifest_batch': MANIFEST_BATCH[pid],
                  'categories_sha256': CATEGORIES_SHA256[pid], 'batches': batches}
    return cases, design, provenance


def pre_source_record(designs):
    return {'schema': 'gamma.request-parallel10-pre-source-freeze.v1', 'problem_ids': list(IDS),
            'source_payload_reads_at_freeze': 0,
            'read_count_scope': 'This preparation command only; later preparation does not restore global blindness or freshness.',
            'original_statement_byte_equivalence': False,
            'manifest_sha256': {str(batch): pin for batch, pin in MANIFEST_SHA256.items()},
            'original_evidence_sha256': ORIGINAL_EVIDENCE,
            'predecessor_observer_sha256': PREDECESSOR_OBSERVER_SHA256,
            'manifest_batch': {str(pid): batch for pid, batch in MANIFEST_BATCH.items()},
            'statement_sha256': {str(pid): oracle_for(pid).STATEMENT_SHA256[pid] for pid in IDS},
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
        raise ValueError('fixed twenty-job population or module pins differ')
    for job in jobs:
        pid, language = job['id'], job['language']; oracle = oracle_for(pid); suffix = 'js' if language == 'javascript' else 'py'
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
    original_evidence(root / 'original-evidence')
    for batch in (4,):
        read_manifest(root / f'original-manifest-batch{batch}.json', batch)
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
    evidence = original_evidence(args.evidence_root)
    rows = {}
    manifest_paths = {4: args.manifest_batch4}
    for batch, path in manifest_paths.items():
        rows.update(read_manifest(path, batch))
    sources = {(pid, lang): args.source_root / rows[pid]['source_files'][lang]['path']
               for pid in IDS for lang in LANGUAGES}
    if any(path.is_symlink() or not path.is_file() for path in sources.values()):
        raise ValueError('all twenty exact source locators must exist before payload access')
    statements, origins, all_cases, designs, provenance = {}, {}, {}, {}, {}
    for pid in IDS:
        origins[pid] = definition_provenance(args.statement_root / str(pid) / 'provenance.json', pid)
        authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'],
                              language='python', payload_kind='statement')
        statements[pid] = q.read(args.statement_root / str(pid) / 'statement.tool-prefix.txt', 131072)
        cases, design, origin = generated(pid, statements[pid])
        all_cases[pid], designs[str(pid)], provenance[str(pid)] = cases, design, origin
    manifest_raws = {batch: q.read(path) for batch, path in manifest_paths.items()}
    if any(q.sha(raw) != MANIFEST_SHA256[batch] for batch, raw in manifest_raws.items()):
        raise ValueError('original manifest changed during preparation')
    args.output.mkdir(parents=True, exist_ok=False)
    for directory in ('sources', 'tests', 'statements'):
        (args.output / directory).mkdir()
    for batch, raw in manifest_raws.items():
        (args.output / f'original-manifest-batch{batch}.json').write_bytes(raw)
    for name, raw in evidence.items():
        target = args.output / 'original-evidence' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    for pid in IDS:
        q.write(args.output / f'tests/{pid}.json', all_cases[pid])
        (args.output / f'statements/{pid}.md').write_bytes(statements[pid])
        (args.output / f'statements/{pid}.provenance.json').write_bytes(origins[pid])
    q.write(args.output / 'case-provenance.json', provenance)
    q.write(args.output / 'pre-source-freeze.json', pre_source_record(designs))
    jobs = []
    for pid in IDS:
        oracle = oracle_for(pid)
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
        'effects': 'Read-only arguments; exact typed scalar, string, or fresh ordered nested-list return; no return-to-input alias.',
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
    for name in ('config', 'manifest-batch4', 'statement-root', 'source-root', 'evidence-root', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--node-runtime', type=Path)
    print(q.encoded(prepare(parser.parse_args())).decode(), end='')
