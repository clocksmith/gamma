"""Freeze fifteen exact F/G/H candidates via the existing imported runner.

Only sanitized metadata selectors are loaded, never historical case manifests.
Original source-blind schemas, later reviews and the G read-accounting limitation
remain immutable evidence. This preparer does not execute or promote candidates.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from . import imported_qualification as q
from .boundary_policy import authorize_before_open
from .known_spec_service import KnownSpecService, _boundary_snapshot

GROUP_IDS = {'f': (3537, 3542, 3573, 3576, 3614),
 'g': (3525, 3552, 3561, 3574, 3599),
 'h': (3534, 3568, 3600, 3613, 3620)}
IDS = (3537, 3542, 3573, 3576, 3614, 3525, 3552, 3561, 3574, 3599, 3534, 3568, 3600, 3613, 3620)
LANGUAGES = ('javascript', 'python')
DOMAIN = 'request-parallel-fgh15-v1'
SELECTOR_FILES = {'f': 'f-selection-v1.json', 'g': 'g-selection-v2.json', 'h': 'h-selection-v1.json'}
SELECTOR_SHA256 = {'f': 'e5d62dcfd474faf2672a613dc408c1366482caa41df7f5823a06a53b125710d7',
 'g': 'ef4d9fae9149853c0a28f965545a788d9cf3c41b98421e3e04c4a7811cc7de61',
 'h': 'b320781c1afc7aa9796cef1aa41f731ff82664501ba44fe7d16dd5eb72f2a688'}
SOURCE_SHA256 = {3525: {'javascript': '85dbd15ca90411ffe493d7b4844edc993f80132641032ca5e399fe1e5a759f8b',
        'python': 'c4d2a1bf5d070daf1f70b758d2e4c3fdbcbe4f5b00d310915de8bde925ce6404'},
 3534: {'javascript': '17371144e947bbbd0910cce094e7a0c094e4f34d160b74fac154cd6fe9ba0a40',
        'python': 'de43241f84e31af02aab7e85460e0f7d49f87a85172662c622cf8b2864e8c019'},
 3537: {'javascript': 'fabee728c1b36eda11196952b59ca0e6cfdd921ead3009c9a86494be07bfff22',
        'python': 'd36f2cc4bc96f1b7cdc740ee842fd5a90e81b0fa143f9e43ae58426d9f418f46'},
 3542: {'javascript': 'fa15d6dc171741f59c41858d84075fd17b0f089265b0b01c91886387ec956f7c',
        'python': '993ccd892acb4dab4f00f2a6475eb3ae4fa4e671ce9a2d26b6b25c05eb694853'},
 3552: {'javascript': '6d4100675c1b6334a2bde0e6c90a3784c1b3a38095371fdf1d55fb4a8685bf15',
        'python': '4293742b75327dc3ac5757972feb9c346b374162c6072942d3e1940fcf92bdef'},
 3561: {'javascript': 'b9064932054a59a55f60c40e710572ef79674329ee3eeabfa58896a82d913644',
        'python': 'a1020ab0ac41c3245f2b6606c2f81e8f43f26f84d76247a1591d3b714bb25f25'},
 3568: {'javascript': '1415953d9120ab120b49f92b870a2f0d72cf379b1e7b0cdbe87bcb3890c56d87',
        'python': '9f3269f112e4fe166bba4952a860620e11ac9cb78943a95b6223817fa8c94184'},
 3573: {'javascript': '1441fdab088a5ec7d9783a52412c71b1dfc706c754a008871e908b3f3d8bf167',
        'python': '91d223db73f4504824d1e3c39fe8b70041487857f62c21aa8d8c3d942812e69f'},
 3574: {'javascript': '9f70dcdc36b7ff5b84c65447a7074cbb6b711718c84dc7fc80c943493e1c1b3b',
        'python': 'e7c2355ca9933f1c0c421c5dd945a15f3b41061d88bc8d06175eab21407f7ef0'},
 3576: {'javascript': '4acd819de875fcd7eacbcde631faa088b54ba79207c4154841b5d5181f07aa38',
        'python': 'a4b6d7884c6e5a593d4d3808d307a133d72ce04174a0fccceec43c3ead2574b2'},
 3599: {'javascript': '8ced561493c2ad37fe04db78581053285180a1a6bb956e53aa2ee0a499d24cae',
        'python': '2aaeb9e7e65b4d0b83b9e05f5baed99df0b3b0d468e1cbf7f57376d8024f6032'},
 3600: {'javascript': '32bd1e40d3a24589f42545c72a2101828d3deab67b45b29ac27a54dd9f259066',
        'python': '1f723e8dc074ee010012f0eef100c4e3194b2bcc6b27852b9763792c57e2b89a'},
 3613: {'javascript': '2cd210a221a3797625e525ac968e7cd8cbd35ee8fd82fb03ea9be6b3adbeda6c',
        'python': 'e0eb05a12d57dbb15a4a90f96e4b7e9f4fc333d292d7a2943e0550af72dbefad'},
 3614: {'javascript': '3913697658aabb01b7986370067b36c18394f007636ecad41640aadbce66972a',
        'python': 'd1e8c233f4c2b2e72aeb57b15f383c5dd8abdada29b67f6e976f477ebc6dc8a2'},
 3620: {'javascript': '46042e2b79342601a48e9b2f048b9237c12c40f36a7112cf213c478fc2ef2652',
        'python': 'efbc3ac8ca0be8a170e43bcabba57ea865dc700c049e66d4e5ad24edcd314f94'}}
ORIGINAL_MANIFEST_METADATA = {3525: {'batch': 3, 'sha256': '7ebff47c314c3d4cd1d3696310c6d97764c7bb8693bc6032a6e73e4a60f4236b'},
 3534: {'batch': 4, 'sha256': '9ac23ea2791681944fb6dcd0e010cb8cde996cde7fca1f9091d70645e8330eec'},
 3537: {'batch': 1, 'sha256': 'ae33e63c7947475febe108a1f871e36cb06592e45b43df3231ccabe6536c496f'},
 3542: {'batch': 3, 'sha256': '7ebff47c314c3d4cd1d3696310c6d97764c7bb8693bc6032a6e73e4a60f4236b'},
 3552: {'batch': 3, 'sha256': '7ebff47c314c3d4cd1d3696310c6d97764c7bb8693bc6032a6e73e4a60f4236b'},
 3561: {'batch': 3, 'sha256': '7ebff47c314c3d4cd1d3696310c6d97764c7bb8693bc6032a6e73e4a60f4236b'},
 3568: {'batch': 3, 'sha256': '7ebff47c314c3d4cd1d3696310c6d97764c7bb8693bc6032a6e73e4a60f4236b'},
 3573: {'batch': 1, 'sha256': 'ae33e63c7947475febe108a1f871e36cb06592e45b43df3231ccabe6536c496f'},
 3574: {'batch': 2, 'sha256': 'd24399c837096d86f9c45b474866ae29a45196992f189e89c7b3644d2639c8f4'},
 3576: {'batch': 3, 'sha256': '7ebff47c314c3d4cd1d3696310c6d97764c7bb8693bc6032a6e73e4a60f4236b'},
 3599: {'batch': 3, 'sha256': '7ebff47c314c3d4cd1d3696310c6d97764c7bb8693bc6032a6e73e4a60f4236b'},
 3600: {'batch': 4, 'sha256': '9ac23ea2791681944fb6dcd0e010cb8cde996cde7fca1f9091d70645e8330eec'},
 3613: {'batch': 4, 'sha256': '9ac23ea2791681944fb6dcd0e010cb8cde996cde7fca1f9091d70645e8330eec'},
 3614: {'batch': 1, 'sha256': 'ae33e63c7947475febe108a1f871e36cb06592e45b43df3231ccabe6536c496f'},
 3620: {'batch': 4, 'sha256': '9ac23ea2791681944fb6dcd0e010cb8cde996cde7fca1f9091d70645e8330eec'}}
PROVENANCE_SHA256 = {3525: '2ecace352b0100c57769925bef6f8d3828f99a3138fdd7deef670748f5d10696',
 3534: 'a774bdb336cc10902686e208148125906b22d913ff3b4d8e23f6296931487604',
 3537: '7cb38cb73949596d43f07c7d49a3ca17b6c2031351434a61b3ff758fe3548164',
 3542: 'c29b864d66dce1a82703f875edffc5bda1a732ef61e6f124b7ab951ff8064024',
 3552: 'afdf3383afde611c4676b3375dea18052d6e678803bd6f8d2240ae84b8625a8e',
 3561: '7916e2d06fc91da0004100e67850bc290239472834e2243b191c1f28f0af2b6c',
 3568: '7b748bf31adb8c0ba4c37601adb5bc832e7628034e1b7c2abd695cf53e0e8bef',
 3573: '13daf8e4dc07e3681cf80c2cb2c3554b0d69c7d65b1926a65e22631a4b36158f',
 3574: '24920cf49ecb1f0751768a1be36a8d79a59d350cec90fb5a0ceb1067777e2bbb',
 3576: '9fbe170c398acdf027248ebdd171a4a01a54f2353992114e418ddc32985db3e4',
 3599: '728966897b94b229faf8497a987d7e9e2ac43bacca07e1eb6dcc2099e6f6c728',
 3600: '68fa479a1963f2a2c4b3e4a67efaf30f358805b89ebe198e39aeaa524800fa9f',
 3613: '034cf4c90159c6e505b948d1ade03f670b47bda0b74f7f77f01b80875112b032',
 3614: '93e4745073daba3df5992c6e10ffb608ebb3784f1ca3db384fa695c12a14ed36',
 3620: '5451da474b5bd9b27b324f5cd801163450f3cbac6081b32d20073dc6554fd905'}
CATEGORIES_SHA256 = {3525: '2d84b5322f26a7b37cc4f636cd974b0900194b2e2382257c6fe5efa19a88835e',
 3534: '20c915cf55be7bfec37a69bb058c28306bef78604eed5427caa9cb17b6dd5510',
 3537: '49adc7b5d4aaadc6582b6bd41029e80ae5d3b3a908eff48cf3ecdbb505230aab',
 3542: '59693bbcd029959f41daae69987eaccf0787cdd6af897f3057590ec37c352279',
 3552: '706c61bf939af71324f38f041aa48c6d9064eac62f2d9169402416f16453ed18',
 3561: '92ae79a720e20cc9453c5c276b175e125d15fa6ffc12006baa79a64d9268f67f',
 3568: 'ebbbffaaee76db08f447775bd0a68dc8bf035a943e46559ececda65b41a255e8',
 3573: '9750a3a3e83f17bab41fa964a64d8123a0ecb7367af4b12628c44c129f3f19cc',
 3574: '0bc401ffb084e7f298be81fa042d4a08e689db7e9e2063007f0e6d5acc6fc02f',
 3576: '259c0238e3627d4109d2e1ab0b171036a9e8d96d34e5722253f807297e7e3b64',
 3599: '55b96b695fca8d2cd20a7c31bdbdc14b6a4fabe55c0d38f6fbcecd44a45d8bb7',
 3600: '96e41a91aad521f5265dccd4b30710b51b0b8dd4519008278e5d39fa9f4856e4',
 3613: 'a9dbd8ae747e3e71c3ee7cfe8d6823999ddac7fd0af23eef5362586ddec189ac',
 3614: '90f53769bdaffc5b1afc43a91dd6652d7ac8072ff1c545443e6f0a5b7d631223',
 3620: 'ce63f34b02bb60e54f6d5791f3e8dfdf15bcf2c5fdca3ae52589f8bc151db36b'}
BATCHES_SHA256 = {3525: '61d5290c63cc56101fde824bea70ebb30a5e3a171f46d3aa1998171d039f7088',
 3534: '44174a639ef6b9b1b01858cbb2eb1b72d7795210df7791cbefdbf51a9d34ea68',
 3537: 'aabd53f4d76af56236d1897e0ff7ef9c9553ebf805001490fe3830d3cff0a56a',
 3542: 'f4a3ec8d4b1d8f48141dc175da07de509dc27acc32770e1cc3d71e3eef566d4a',
 3552: '43aa89376c15746bb9d037b74d092c17672a0c3948e669d755be9668184861e5',
 3561: '799a78c541152c552a0e9be534f0f064dfb544b6ebecd3ff8e09decf25cf84f7',
 3568: '041c8d7226dec2a453e25bebdfc43259c95fa9ce6e09ae9c58f11232d1a818ed',
 3573: '88365df3ab8d435da015dd8a86041bc7fbb76b39d7db1d52cf5cc465ed08174d',
 3574: '8ca31a8df5cae7f2c9b6fcdefdfb540aae9786117cabf46b4d0f4b8d1f3f877b',
 3576: '125688abaf04fca10299d53feee28810121145c5025352df63beafa22dbcd110',
 3599: 'baa9bcbd1298f5e04dfdc9e4dd7be8bfa9d5f3e4e941ddb47106845be035684e',
 3600: 'bbc9a9126e7db558b10a422e45a90b42a0b1e3cb1817e609c6b75ffcce005606',
 3613: 'c522bcd390e4903d0dc7bb484a873ccb1d954ac2b90342e1640b64cc86c4b827',
 3614: 'edb542db4ddeee4308eb0ed0cf1648563a722adfd22ed157538b27dd264270e1',
 3620: '4f03a0d1b4646792d073fa569fe50d9a54e1f83af4db404d72b405a36d429e9c'}
ORIGINAL_EVIDENCE = {'f': {'definition-index.json': '3dfa946859f6018bea74c6d3b44c10dce370b4a240eabc98c01a9fcd2de6c291',
       'first-static-review.json': '6c2b8a0225f77729bc10e3614f8ec3b905c85e42d3c1e32eb47cd55ad9b9fb97',
       'independent-review.json': 'e39ad4d13abdd958d3ffbcdba59e918c6837770ce984eedabfecb85d7d49e907',
       'original-freeze.json': '3a9275aefd95cb2876c50165eac86054376f06493f9a9366eefc15dbaf7219f9',
       'preserved-author-freeze-v1.json': 'acccb7450a1ca2daa32c9d7ea18a554aae0d2839f98b70e01a4ab22e4eeaaaef',
       'second-static-review.json': 'b56cc37d19de759834077d1689975f2944bda29f69618990a4c12f02bb4dff7f',
       'source-acquisition.json': '366112240d83d678c57c018200945f88e033e69d3ead17363c92bc8c6d71d930'},
 'g': {'definition-accounting-clarification.json': '9052ef1553b9290579fa5021e9280a073e498a33389dcee7c26dc17300aae36b',
       'definition-index.json': 'aee03682e8805d1da69e6f636bae177b7e2e3149c039e5e754b1f6257740a58f',
       'first-static-review.json': '48f01f10887d2ffd52f1d4357db2cacccd4b74c4821bd772229b7892cbd1276a',
       'independent-review.json': 'c27ddaf59fe51bb34a7e40c50b6bf4845f7512bc0d5317a9970c3b471f511853',
       'original-freeze.json': '20c40bbbd1df79ac5aeb7542effa3179430dc2a345d11a956b2e8e1f94bf6b00',
       'second-static-review.json': '160c691fdd62e2f11fdec898130dd77952584f89e7ff7e0749b8025dfa20d8d9',
       'source-acquisition.json': '16c83001320d320aa1a0c15947a1ec8c8302fafe0c1b5796578cc932c21e55cf'},
 'h': {'definition-index.json': '0e6eddc3cea5a512f9cf5c90402d8e48cf6109407725e9592826593940c64c3c',
       'first-static-review.json': '809483212990dccf98d1433e00bbae299672b7e5fc20f988c84b6e727bfa09ff',
       'independent-review.json': 'ac7cf74f01d15aa0f54dd68cf6f952fc9ab792056368f83d414f8ab020be18e6',
       'original-freeze.json': '975709c07dffb73192bdad95c4086cb51b927c9795a778b6c787c7f3ad305be0',
       'second-static-review.json': '5fe026df3e16526260fc43bffda6b4f5625c2c5bf46b5855691b2d8f94711651',
       'source-acquisition.json': '83e1cf7aa29ae183a93f4ed8ca8ba202f41faebe4e1c52f77ba2c6ba3277dd33'}}
DEFINITION_INDEX_SHA256 = {'f': '3dfa946859f6018bea74c6d3b44c10dce370b4a240eabc98c01a9fcd2de6c291',
 'g': 'aee03682e8805d1da69e6f636bae177b7e2e3149c039e5e754b1f6257740a58f',
 'h': '0e6eddc3cea5a512f9cf5c90402d8e48cf6109407725e9592826593940c64c3c'}
PREDECESSOR_OBSERVER_SHA256 = '6147c8eba2d124e56cb5eac4dde27f880b09e3b148abe9d02d44e930686dcc48'


def group_for(pid):
    if type(pid) is not int or pid not in IDS:
        raise ValueError('problem outside fixed F/G/H population')
    return next(group for group, ids in GROUP_IDS.items() if pid in ids)


def oracle_for(pid):
    group = group_for(pid)
    from . import request_parallel_f_oracles as f
    from . import request_parallel_g_oracles as g
    from . import request_parallel_h_oracles as h
    return {'f': f, 'g': g, 'h': h}[group]


def validate(pid, args):
    oracle_for(pid).validate(pid, args)


def read_selection(path, group):
    raw = q.read(path)
    if group not in SELECTOR_SHA256 or q.sha(raw) != SELECTOR_SHA256[group]:
        raise ValueError('sanitized selector pin differs')
    value = q.decode(raw)
    rows = value.get('selected', [])
    if (len(rows) != 5 or {row.get('problem_id') for row in rows} != set(GROUP_IDS[group]) or
            value.get('legacy_case_or_reasoning_fields_supplied_to_oracle_authors') is not False):
        raise ValueError('fixed selector population missing, duplicated, extra or unsanitized')
    for row in rows:
        pid = row['problem_id']
        if tuple(row.get('parameters', [])) != oracle_for(pid).PARAMETERS[pid]:
            raise ValueError('ordered source parameters differ')
        if {key: row['manifest'].get(key) for key in ('batch', 'sha256')} != ORIGINAL_MANIFEST_METADATA[pid]:
            raise ValueError('original manifest metadata differs; no manifest payload read is permitted')
        for language, suffix in (('javascript', 'js'), ('python', 'py')):
            if row['source_files'].get(language) != {'path': f'{language}/{pid}.{suffix}', 'sha256': SOURCE_SHA256[pid][language]}:
                raise ValueError('selector exact source binding differs')
    return {row['problem_id']: row for row in rows}, raw


def additional_code():
    paths = [Path(__file__), *(Path(__file__).with_name(f'request_parallel_{group}_oracles.py')
                               for group in GROUP_IDS), Path(__file__).with_name('imported_clean_domains.py')]
    return {str(path.resolve()): q.file_hash(path) for path in paths}


def _source_rows(group, name, value):
    """Read only the three known immutable schemas, never invent review fields."""
    if (group == 'g' and name == 'first-static-review.json') or (group == 'f' and name == 'second-static-review.json'):
        return [(row['problem_id'], source['language'], source['sha256'])
                for row in value['problems'] for source in row['sources']]
    if group == 'g' and name == 'source-acquisition.json':
        return [(row['problem_id'], row['language'], row['sha256']) for row in value['operations']]
    key = ('reviewed_sources' if (group == 'g' and name == 'second-static-review.json') or
           (group == 'h' and name == 'first-static-review.json') else
           'implementations' if group == 'h' and name == 'second-static-review.json' else 'rows')
    rows = value[key]
    for row in rows:
        if (row.get('blocking_static_defect') is not None or row.get('blocking_static_defect_found') is True or
                row.get('static_blocker_found') is True):
            raise ValueError('retained source review reports a blocking defect')
    return [(row['problem_id'], row['language'], row['source']['sha256'] if group == 'g' else row['source_sha256'])
            for row in rows]


def original_evidence(root):
    retained = {}
    raw = q.read(root / 'observer-predecessor.py')
    if q.sha(raw) != PREDECESSOR_OBSERVER_SHA256:
        raise ValueError('archived pre-source observer differs')
    retained['observer-predecessor.py'] = raw
    for group, ids in GROUP_IDS.items():
        values = {}
        for name, pin in ORIGINAL_EVIDENCE[group].items():
            raw = q.read(root / group / name)
            if q.sha(raw) != pin:
                raise ValueError('immutable original evidence drift')
            retained[group + '/' + name] = raw
            values[name] = q.decode(raw)
        frozen, review = values['original-freeze.json'], values['independent-review.json']
        link = 'pre_source_freeze' if group == 'f' else 'freeze'
        if (review.get(link, {}).get('sha256') != ORIGINAL_EVIDENCE[group]['original-freeze.json'] or
                review.get('candidate_executions') != 0 or not review.get('reviewer') or
                frozen.get('source_payload_reads_at_freeze' if group == 'f' else 'source_payload_reads') != 0 or
                frozen.get('candidate_executions') != 0):
            raise ValueError('original independent approval or source-blind chronology differs')
        oracle = oracle_for(ids[0])
        if group == 'f':
            rows = frozen['problems']
            code_pin = frozen['oracle_module']['sha256']
            observer_pin = frozen['serialization_dependency']['sha256']
            index_pin = frozen['definition_index']['sha256']
            if frozen['preserved_author_freeze']['sha256'] != ORIGINAL_EVIDENCE[group]['preserved-author-freeze-v1.json']:
                raise ValueError('preserved original F freeze link differs')
        else:
            rows = frozen['cases']
            code = {Path(row['path']).name: row['sha256'] for row in frozen['code']}
            dependencies = {Path(row['path']).name: row['sha256'] for row in frozen['dependencies']}
            code_pin = code.get(f'request_parallel_{group}_oracles.py')
            observer_pin = dependencies.get('imported_qualification.py')
            index_pin = frozen['definition_pins']['sha256']
            if frozen.get('ids') != list(ids):
                raise ValueError('original fixed group identities differ')
            for name, pin in dependencies.items():
                if name != 'imported_qualification.py' and q.file_hash(Path(__file__).with_name(name)) != pin:
                    raise ValueError('original frozen helper drift')
        if (code_pin != q.file_hash(oracle.__file__) or observer_pin != PREDECESSOR_OBSERVER_SHA256 or
                index_pin != DEFINITION_INDEX_SHA256[group] or
                ORIGINAL_EVIDENCE[group]['definition-index.json'] != index_pin):
            raise ValueError('original oracle, definition index or predecessor identity differs')
        if [row['problem_id'] for row in rows] != list(ids):
            raise ValueError('original group population differs')
        for row in rows:
            pid = row['problem_id']
            if group == 'f':
                count, case_pin, category_pin, batch_pin = row['cases'], row['cases_file']['sha256'], row['categories_file']['sha256'], row['batches_file']['sha256']
            elif group == 'g':
                count, case_pin, category_pin, batch_pin = row['case_count'], row['cases_sha256'], row['categories_sha256'], row['batches_sha256']
            else:
                pins = {Path(item['path']).name: item['sha256'] for item in row['artifacts']}
                count, case_pin = row['cases'], row['case_sha256']
                category_pin, batch_pin = pins[f'{pid}.categories.json'], pins[f'{pid}.batches.json']
            if (count != oracle.CASE_COUNT[pid] or case_pin != oracle.CASES_SHA256[pid] or
                    category_pin != CATEGORIES_SHA256[pid] or batch_pin != BATCHES_SHA256[pid]):
                raise ValueError('original case, category or exact grouping differs')
        wanted = sorted((pid, language, SOURCE_SHA256[pid][language]) for pid in ids for language in LANGUAGES)
        for name in ('source-acquisition.json', 'first-static-review.json', 'second-static-review.json'):
            if values[name].get('candidate_executions') != 0 or sorted(_source_rows(group, name, values[name])) != wanted:
                raise ValueError('original acquisition or static source binding differs')
        if group == 'g':
            clarification = values['definition-accounting-clarification.json']
            if (clarification.get('problem_id') != 3574 or
                    clarification.get('newly_written_statement_descriptor_hash_reads') != 3 or
                    clarification.get('newly_written_transport_descriptor_hash_reads') != 1 or
                    clarification.get('fresh_gate_rerun_immediately_before_each_of_these_four_local_hash_reads') is not False or
                    clarification.get('source_payload_reads_before_oracle_approval') != 0):
                raise ValueError('G read-accounting limitation was relabeled')
    return retained


def definition_provenance(path, pid):
    raw = q.read(path, 131072)
    if q.sha(raw) != PROVENANCE_SHA256[pid]:
        raise ValueError('new definition provenance drift')
    value, group = q.decode(raw), group_for(pid)
    if value.get('problem_id') != pid:
        raise ValueError('definition identity differs')
    if group == 'f':
        pin = value.get('statement_prefix', {}).get('sha256')
        valid = value.get('original_statement_byte_equivalence_claimed') is False and value.get('original_statement_byte_pin') is None
    elif group == 'g':
        pin = value.get('statement', {}).get('sha256')
        key = 'original_statement_byte_equivalence_claimed' if pid == 3574 else 'original_statement_byte_equivalence'
        valid = value.get(key) is False
    else:
        pin = value.get('statement_sha256')
        valid = value.get('original_definition_byte_identity_available') is False
    if not valid or pin != oracle_for(pid).STATEMENT_SHA256[pid]:
        raise ValueError('new definition provenance representation differs')
    return raw


def batch_manifest(cases, oracle, *, original_group=None):
    if original_group == 'g':
        return list(q.batches(cases))
    field = 'expected_stdout_bytes' if original_group == 'f' else 'projected_success_stdout_bytes'
    return [{'offset': offset, 'calls': len(batch), 'packet_bytes': len(q.encoded(q.packet(batch))),
             'packet_sha256': q.sha(q.encoded(q.packet(batch))),
             field: {language: oracle.expected_observation_bytes(batch, language) for language in LANGUAGES}}
            for offset, batch in q.batches(cases)]


def generated(pid, statement):
    oracle = oracle_for(pid)
    if q.sha(statement) != oracle.STATEMENT_SHA256[pid]:
        raise ValueError('new statement snapshot drift')
    cases, categories = oracle.build_cases(pid, statement)
    if (len(cases) != oracle.CASE_COUNT[pid] or q.sha(q.encoded(cases)) != oracle.CASES_SHA256[pid] or
            q.sha(q.encoded(categories)) != CATEGORIES_SHA256[pid] or
            type(categories) is not list or len(categories) != len(cases) or
            any(type(category) is not str or not category for category in categories)):
        raise ValueError('hard-pinned generated cases or categories differ')
    for case in cases:
        oracle.validate(pid, case['args'])
    if len(q.encoded(cases)) > q.MAX_FILE:
        raise ValueError('generated case file exceeds unchanged reader cap')
    original = batch_manifest(cases, oracle, original_group=group_for(pid))
    if q.sha(q.encoded(original)) != BATCHES_SHA256[pid]:
        raise ValueError('original frozen grouping or output projection differs')
    projection = batch_manifest(cases, oracle)
    if any(size > q.LIMITS['max_output_bytes'] for row in projection for size in row['projected_success_stdout_bytes'].values()):
        raise ValueError('projected observations exceed unchanged cap')
    design = {'case_count': len(cases), 'tests_raw_sha256': oracle.CASES_SHA256[pid],
              'batch_count_per_language': len(projection), 'original_batches_sha256': BATCHES_SHA256[pid],
              'batch_projection_sha256': q.sha(q.encoded(projection)),
              'largest_packet_bytes': max(row['packet_bytes'] for row in projection)}
    provenance = {'categories': categories, 'counts': dict(Counter(categories)),
                  'statement_provenance_sha256': PROVENANCE_SHA256[pid],
                  'original_manifest_metadata': ORIGINAL_MANIFEST_METADATA[pid],
                  'categories_sha256': CATEGORIES_SHA256[pid], 'batches': projection,
                  'original_batches_sha256': BATCHES_SHA256[pid],
                  'projection_scope': 'Additive metadata projection; original schema and grouping remain immutable.'}
    return cases, design, provenance


def pre_source_record(designs):
    return {'schema': 'gamma.request-parallel-fgh15-pre-source-freeze.v1', 'problem_ids': list(IDS),
            'source_payload_reads_at_freeze': 0,
            'read_count_scope': 'This preparation command only; it does not restore global blindness or freshness.',
            'original_statement_byte_equivalence': False,
            'selector_sha256': SELECTOR_SHA256, 'original_evidence_sha256': ORIGINAL_EVIDENCE,
            'original_manifest_metadata': {str(pid): entry for pid, entry in ORIGINAL_MANIFEST_METADATA.items()},
            'historical_manifest_payloads_loaded': False,
            'predecessor_observer_sha256': PREDECESSOR_OBSERVER_SHA256,
            'statement_sha256': {str(pid): oracle_for(pid).STATEMENT_SHA256[pid] for pid in IDS},
            'statement_provenance_sha256': {str(pid): PROVENANCE_SHA256[pid] for pid in IDS},
            'expected_source_sha256': {str(pid): SOURCE_SHA256[pid] for pid in IDS},
            'generated_cases': designs, 'additional_code': additional_code(), 'observer_code': q.code_pins(),
            'limits': q.LIMITS, 'max_packet_bytes': q.MAX_PACKET,
            'G_acquisition_accounting': 'Four historical local 3574 descriptor reads reused an existing authorization rather than rerunning the gate each time; immutable clarification retained, not retroactively relabeled.'}


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
    for group in GROUP_IDS:
        read_selection(root / 'selectors' / SELECTOR_FILES[group], group)
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
    rows, selection_raws = {}, {}
    for group in GROUP_IDS:
        selected, raw = read_selection(args.selection_root / SELECTOR_FILES[group], group)
        rows.update(selected)
        selection_raws[group] = raw
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
    args.output.mkdir(parents=True, exist_ok=False)
    for directory in ('sources', 'tests', 'statements', 'selectors'):
        (args.output / directory).mkdir()
    for group, raw in selection_raws.items():
        (args.output / 'selectors' / SELECTOR_FILES[group]).write_bytes(raw)
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
    for name in ('config', 'selection-root', 'statement-root', 'source-root', 'evidence-root', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--node-runtime', type=Path)
    print(q.encoded(prepare(parser.parse_args())).decode(), end='')
