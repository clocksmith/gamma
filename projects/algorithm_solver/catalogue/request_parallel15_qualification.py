"""Freeze the fixed parallel fifteen request candidates for the existing imported runner.

Only newly generated public-definition cases are admitted here. Original source
bytes remain separate from new statement snapshots: current pinned web-tool
prefixes do not establish byte equivalence to historical representations. This
module neither executes nor promotes candidates.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from . import imported_qualification as q
from .boundary_policy import authorize_before_open
from .known_spec_service import KnownSpecService, _boundary_snapshot

IDS = (3223, 3232, 3532, 3583, 3612, 3517, 3531, 3567, 3598, 3618, 3524, 3551, 3587, 3608, 3619)
LANGUAGES = ('javascript', 'python')
DOMAIN = 'request-parallel15-v1'
MANIFEST_SHA256 = {2: 'd24399c837096d86f9c45b474866ae29a45196992f189e89c7b3644d2639c8f4',
 3: '7ebff47c314c3d4cd1d3696310c6d97764c7bb8693bc6032a6e73e4a60f4236b'}
MANIFEST_BATCH = {3223: 3,
 3232: 3,
 3532: 3,
 3583: 3,
 3612: 3,
 3517: 2,
 3531: 2,
 3567: 2,
 3598: 2,
 3618: 2,
 3524: 2,
 3551: 2,
 3587: 2,
 3608: 2,
 3619: 3}
SOURCE_SHA256 = {3223: {'javascript': '44d2764566a4d2c54819a9a8ed1f4e43678684a502ca5aa1335bc2d5d7434e1c',
        'python': 'dfc64c1e07a6e224418071b721fb6b0d35774ac123e3f16aedc568cb3671d47c'},
 3232: {'javascript': 'da490592837e9363f075070cccd13cee83291613149f677ea66d250f8e04154b',
        'python': 'bb14ba0f2590486516e83ecc7ea95e1c477d3e4bfa13f2b830b660d654b89dad'},
 3532: {'javascript': '5d62c36eac2a7f81a779eddc12267419a0463a08f5cda233b4feaa1dc5af1776',
        'python': 'c2eb371ccef69bc1b660c014671a900ead67ee5909b2f6c980b097eead0bc093'},
 3583: {'javascript': 'b01eb7251cf8335f8ddc49d208845a5092604fc888fdb9f8cb117ebc3784b762',
        'python': 'b9c5dc6cd04a57f4e50fc948811cfaadf3e6e680bfa232cd11e6dc1add056ea8'},
 3612: {'javascript': 'bf2e7380ba9cda96910123ba41a2fc365117c7f4c3bafe70d12e89de782cd4b8',
        'python': 'f51ea1c82969cc46d32f69e17f7dcd76073e137746eb9956837594815eb8ee6b'},
 3517: {'javascript': '15eb47769d6701c497fbed3c645b8c18221dc610e036c1bb89fcf2cdc306d15b',
        'python': '7471267e03cb312320e863cbacab2a6cd1ddd8f566a0f2891188929f15f8c1cc'},
 3531: {'javascript': '192c6af678cd51aeaa753e0da08f4f4c5be6776325c295abca2c09b4b72cdfa8',
        'python': 'fc2f926f65f7814b7be20a2ed2ad537643abdb6d01d82009dd68cc57cc330968'},
 3567: {'javascript': 'cf625ec8b7acb314fbc8c2840631104c10d3521b5dca053715da40f61a528e3d',
        'python': '277450454465b94abdd89fdc0ba366781bb315786a407aba1ba132a86fb22e0c'},
 3598: {'javascript': '9245c4b6e0634d2cc519fb71091504361256ba6530b5f877c4435192a5f1b2db',
        'python': 'c7efbbbb4ba5d2264f5dcd7314ed658d7a704ad6ae729100dcfbd2c109d3d70b'},
 3618: {'javascript': 'c7c813b2d8d3adbeafd560d850b421a396f888e09facd33e6dc3cfec1ac8db0f',
        'python': 'f025c11f151269b0f52e77ecfe9301bb66d1347bb41757651a9a542c21fe9474'},
 3524: {'javascript': '5dcb2ff20cdd808284bf1429f6b3eaa872c05736031d7098f7f2a5cbbc5146b4',
        'python': '8d9180d48869d8a815ba40f53d8444323291090429b417129162bbd31500941f'},
 3551: {'javascript': 'e50d0399178ea5b7727e7574e462eec0735fcecde8be2e88bf2a198915961f00',
        'python': 'fc1ea519c9febc0f58f5f89f2a9f2ef1695cc62e55d4976b4a0c2667e3666621'},
 3587: {'javascript': '601c383d98f5b7d922002a9d35ebfbd875ebb0e56ed8e4edc2bf8cbb297dda8c',
        'python': '29c04fa37e0a7858d154de4ade3f154643a17fc54eac4796c1820f18823089fa'},
 3608: {'javascript': 'fe4c6aeca04d6a146c5e20f1b51b996442b19cca1a406ace31c2f880af3ebfe0',
        'python': '26932b02f85b47d6409e237c8cfb0b936ae5b92d59deadcd98c493c7803bc934'},
 3619: {'javascript': '95addd205f73482ea2e9774f23271d56ede3014ec8e04ad412f52467a0b9988e',
        'python': '24460827982b2b235b7c19b4056597b920f48541f288ff73939a625cdda883dd'}}
PROVENANCE_SHA256 = {3223: '170ed7a6a464b25141b3b4a7cd11f3b943f4bcf6945dc24099514ddad1c14aa4',
 3232: 'cc8ba5a87b83e8058c3d54421ed709484c44af8659cac70b67305a122041bcc1',
 3532: '930679c8305427e573043fad462275bd485f27103113cd0194de6b53cab83b95',
 3583: 'f908c2d964dee3088c6b0173d1bec3934fe78369e4350bf21867bad4838d8f31',
 3612: 'c245a1f77348be6d0946dbad6bf19ca16dddf66712c67d1ac722c4c75802b1b1',
 3517: '68086281a035e352074ebea3c5b3ad6da2a9e03f3ef218d666c3bff81b592c12',
 3531: '1dc02a1b75a4456b904a31dd2273b290a6263e231dcbab7132131b2433342457',
 3567: '8248821588d1acd93e478b97b222ec307cb1710ec18c1986ee6cbb5a6a8c4fa2',
 3598: '43453fb7b070f7dfad20b321764a28f04f6c919b827d3817663b3bfb77f62970',
 3618: '70da09714b25c64cf5611d7ae526d546fddfbae42fbb411f239d1794db23c60c',
 3524: '5f633c4f1f9b90a217c76c5b970d8f5706987d988fdd99ad402fbf176d66d2e1',
 3551: '9012bf1c757e083890a811f8b1eee1ff59352734c209dae49698a287ba2d25f5',
 3587: '484e9e6353fedd5d9aedd4eef9fa2f314db8fbad341789f9761e5e478671bbc8',
 3608: '341f5242e31a711440854a448497f2233ffc92c7566b3dd9ca007b074415b9ff',
 3619: 'fb4c0bb85d06f5ba07299d18a808e397b6c3c8a65d90a0e03016a77b4be38876'}
CATEGORIES_SHA256 = {3223: '47aacc43d6707c9fea53065b780f7394b3ad3fd20863dd0178b4985a63596914',
 3232: '6ea54e596427c9c695276d0e6502620176c598bdd1d0bc18f3cfdd5df882b617',
 3532: '3835265b650b33667e68a154df9d2a21bccb0b2f2e2a4d7bea66da9e0f6b9223',
 3583: '7cb98d5b14a6e22fade0e20aaff2562dbc4a21c666c5fb3029c39fa14146948e',
 3612: '11fdea9b5d26742af7080bdb36cb1e8170c7f3a3c86c26266efb7a11601b9a52',
 3517: 'ad9432f65681f117cb2cd62b7de9d86b7331642ad1a0db2ecd4a2542bc366d87',
 3531: '12f4b88432835614c03fd8c3a1ccbfbaddb7d3e0f3a6086d5c2a991887b2dbd8',
 3567: 'd6433e9f5b558ae7bb669a5a0c89f4f86b515901c60a0df32efa8842f7207b0b',
 3598: 'df39bebad297863978fa35f42f91d7ad67cb5bc1b81662b6a8914e7437116ae1',
 3618: 'fdd076fdcdf2d10d7f0bb1d6611f250197c0018f82f36ab62135b92892b51d23',
 3524: '867de83ee629b0c343a4cac329b4ab83237df9a3bd23420dc3251491b0091028',
 3551: '80e8670baca965226a8923f69f50aaffaea5916a63ed14153f0eb1c3d342ad63',
 3587: 'a5443f712bddaabdc0880a94e71c38d5814549a857d2b151360aef3905cbf429',
 3608: 'd0a2fbad098374d107c426c91e4411327fcbb9dff6b2173e3e5783ba08951f40',
 3619: '9ea88830aa40e1abe87073ea27844dcf913fb708520c6ac5cb8abf3d1eaafa2e'}
ORIGINAL_EVIDENCE = {'a': {'original-freeze.json': 'f71f9b1c5c0bd6b844a4385a3ecc6645b2c20059613f5f5bd6a1ceab59163512',
       'independent-review.json': 'f63e58153219365cce5f99018b6ae521d4220bbebd311ee3eb945201fd96a752'},
 'b': {'original-freeze.json': '8133be5618c343ded9004d5983849a58e9d21b9fe7dc3702ae3eddccfe18902f',
       'independent-review.json': '3048b07be12d372b1575f7fe460066dc5501b9b6842f7620bcf474c886773c65'},
 'c': {'original-freeze.json': 'a5c5918299acf7c623442a85450afb910ab4dddf33ba268e8ddbf6a347689edd',
       'independent-review.json': 'f8af7492c8ee41f990240465c2eab8f1816bc4b7bb55d8060c9ed8fdbc35087d'}}
DEFINITION_INDEX_SHA256 = {'a': 'd718a21c2ba8782b51eee306eee7162604368e871ad27bf7e6dd7a84af19ea47',
 'b': '75a9bafe53297dc3b342088104f794f5a9da2287163502ac8aa2050f885208a8',
 'c': '0713d9f05cd1318839fbde445441442069bc70428925f65d339f50d9acc5591a'}


def oracle_for(pid):
    from . import request_parallel_a_oracles as a
    from . import request_parallel_b_oracles as b
    from . import request_parallel_c_oracles as c
    if type(pid) is not int or pid not in IDS:
        raise ValueError('problem outside the fixed fifteen-ID lane')
    if pid in IDS[:5]:
        return a
    if pid in IDS[5:10]:
        return b
    return c


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
                               for group in ('a', 'b', 'c')),
             Path(__file__).with_name('imported_clean_domains.py')]
    return {str(path.resolve()): q.file_hash(path) for path in paths}


def original_evidence(root):
    """Read original metadata in its three schemas, without relabeling history."""
    retained = {}
    for offset, group in enumerate(('a', 'b', 'c')):
        values = {}
        for name, expected in ORIGINAL_EVIDENCE[group].items():
            raw = q.read(root / group / name)
            if q.sha(raw) != expected:
                raise ValueError('original source-blind freeze or independent approval drift')
            retained[group + '/' + name] = raw
            values[name] = q.decode(raw)
        frozen, reviewed = values['original-freeze.json'], values['independent-review.json']
        link = reviewed.get('approved_freeze' if group == 'c' else 'freeze', {})
        if (link.get('sha256') != ORIGINAL_EVIDENCE[group]['original-freeze.json'] or
                frozen.get('problem_ids' if group == 'b' else 'ids') != list(IDS[offset * 5:offset * 5 + 5]) or
                reviewed.get('candidate_executions') != 0 or not reviewed.get('reviewer')):
            raise ValueError('original independent approval does not bind its group')
        if group == 'c':
            rows = frozen['problems']; oracle_pin = frozen['oracle_module']['sha256']
            index_pin = frozen['definition_index']['sha256']
            if frozen.get('source_payload_reads_at_freeze') != 0:
                raise ValueError('original C freeze was not source-blind')
        elif group == 'b':
            rows = frozen['cases']; oracle_pin = frozen['oracle_module']['sha256']
            index_pin = frozen['new_definition_pins']['sha256']
            if frozen.get('source_payload_reads_for_selected_ids_at_freeze') != 0:
                raise ValueError('original B freeze was not source-blind')
        else:
            rows = frozen['cases']
            oracle_pin = next(row['sha256'] for row in frozen['code']
                              if Path(row['path']).name == f'request_parallel_{group}_oracles.py')
            index_pin = frozen['definition_pins']['sha256']
            if frozen.get('candidate_source_reads') != 0:
                raise ValueError('original A freeze was not source-blind')
            helper_pin = next(row['sha256'] for row in frozen['dependencies']
                              if Path(row['path']).name == 'imported_clean_domains.py')
            if q.file_hash(Path(__file__).with_name('imported_clean_domains.py')) != helper_pin:
                raise ValueError('original full-domain helper drift')
        oracle = oracle_for(IDS[offset * 5])
        if q.file_hash(oracle.__file__) != oracle_pin or index_pin != DEFINITION_INDEX_SHA256[group]:
            raise ValueError('original oracle or definition index differs')
        for row, pid in zip(rows, IDS[offset * 5:offset * 5 + 5]):
            if (row.get('id' if group == 'c' else 'problem_id') != pid or
                    row.get('case_count' if group == 'c' else 'cases') != oracle.CASE_COUNT[pid] or
                    row['cases_sha256'] != oracle.CASES_SHA256[pid] or
                    row['categories_sha256'] != CATEGORIES_SHA256[pid]):
                raise ValueError('original fixed case or category population differs')
        if len(rows) != 5:
            raise ValueError('original group population differs')
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
        valid = (value.get('statement', {}).get('sha256') == oracle.STATEMENT_SHA256[pid] and
                 value.get('historical_statement_byte_equivalence_claimed') is False and
                 value.get('raw_html_equivalence_claimed') is False and
                 value.get('numeric_heading_title_and_alias_checked') is True)
    elif pid in IDS[5:10]:
        valid = (value.get('statement_prefix', {}).get('sha256') == oracle.STATEMENT_SHA256[pid] and
                 value.get('original_statement_byte_equivalence_claimed') is False and
                 value.get('original_definition_byte_pin') is None and
                 value.get('numeric_heading_checked') is True and value.get('slug_title_checked') is True and
                 value.get('original_manifest_sha256') == MANIFEST_SHA256[MANIFEST_BATCH[pid]])
    else:
        valid = (value.get('new_statement_prefix_sha256') == oracle.STATEMENT_SHA256[pid] and
                 value.get('original_statement_equivalence_established') is False and
                 value.get('original_definition_prefix_sha256') is None and
                 value.get('original_manifest_sha256') == MANIFEST_SHA256[MANIFEST_BATCH[pid]])
    if not valid:
        raise ValueError('new definition provenance representation differs')
    return raw


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
    design = {'case_count': len(cases), 'tests_raw_sha256': oracle.CASES_SHA256[pid],
              'batch_count_per_language': len(groups),
              'largest_packet_bytes': max(len(q.encoded(q.packet(batch))) for _, batch in groups)}
    provenance = {'categories': categories, 'counts': dict(Counter(categories)),
                  'statement_provenance_sha256': PROVENANCE_SHA256[pid],
                  'original_manifest_batch': MANIFEST_BATCH[pid],
                  'categories_sha256': CATEGORIES_SHA256[pid]}
    return cases, design, provenance


def pre_source_record(designs):
    return {'schema': 'gamma.request-parallel15-pre-source-freeze.v1', 'problem_ids': list(IDS),
            'source_payload_reads_at_freeze': 0,
            'read_count_scope': 'This preparation command only; later preparation does not restore global blindness or freshness.',
            'original_statement_byte_equivalence': False,
            'manifest_sha256': {str(batch): pin for batch, pin in MANIFEST_SHA256.items()},
            'original_evidence_sha256': ORIGINAL_EVIDENCE,
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
        raise ValueError('fixed thirty-job population or module pins differ')
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
    for batch in (2, 3):
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
    manifest_paths = {2: args.manifest_batch2, 3: args.manifest_batch3}
    for batch, path in manifest_paths.items():
        rows.update(read_manifest(path, batch))
    sources = {(pid, lang): args.source_root / rows[pid]['source_files'][lang]['path']
               for pid in IDS for lang in LANGUAGES}
    if any(path.is_symlink() or not path.is_file() for path in sources.values()):
        raise ValueError('all thirty exact source locators must exist before payload access')
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
    for name in ('config', 'manifest-batch2', 'manifest-batch3', 'statement-root', 'source-root', 'evidence-root', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--node-runtime', type=Path)
    print(q.encoded(prepare(parser.parse_args())).decode(), end='')
