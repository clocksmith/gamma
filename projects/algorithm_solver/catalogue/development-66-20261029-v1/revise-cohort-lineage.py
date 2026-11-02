"""Rebind cohort lineage after reviewed source/semantics/contract corrections.

For each development cohort this reconciles hash-bound metadata with the bytes on
disk, without rewriting history:

1. pre-source-reference-freeze.json: appends an amendment (old -> new hash, change,
   reason) for every reviewed file in REVISIONS whose bytes differ from the manifest
   pin, and refreshes `current_sha256` where that map exists.
2. study-history/blobs/<old>.bin: archives the superseded source/semantics bytes
   (recovered from Git when no blob exists yet).
3. manifest.json: each source_inventory row whose source or semantics hash differs
   from disk gets the current hashes plus an appended `supersedes` entry naming
   the prior hashes, prior catalog variant ID, amendments and blob paths; the
   `files` hashes are recomputed.
4. authoring-catalog.json: only revised variants change. Their prior record is kept
   under `supersedes`; the revised variant ID is the SHA-256 of the sort-keyed
   compact JSON of the record without `variant_id`/`supersedes` (the original
   generator's rule is not recorded in this repository, so prior IDs stay opaque).
5. SHA256SUMS: recomputed for its listed paths.

No qualification, admission or expected-value authority changes. Re-running with
no byte changes is a no-op.

Run: python3 revise-cohort-lineage.py
"""
from pathlib import Path
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
AUTHORED = ROOT / 'projects/algorithm_solver/catalogue/authored'
AT = '2026-11-02'
NATIVE_156 = ('Native-ABI split: solve deep-copies a native TreeNode input (iterative, seen map rejects a node reached '
              'twice) so it neither mutates nor aliases caller nodes; upsideDownBinaryTree / Solution.upsideDownBinaryTree '
              'rotates the caller graph in place.')
NATIVE_280 = ('Native-ABI split: wiggleSort / Solution.wiggleSort now rewrites nums in place and returns nothing '
              '(in_place_arg 0); solve still returns a new list and leaves nums unchanged.')
REASONS = {
    'requested-156-1940-31-20261028-v1': {
        'contracts.json': ('280 official_interface gains in_place_arg 0', 'declare the official in-place ABI so the runner judges nums after the call'),
        'python/156.py': (NATIVE_156, 'solve previously rotated a native TreeNode input in place and returned caller nodes'),
        'javascript/156.js': (NATIVE_156, 'solve previously rotated a native TreeNode input in place and returned caller nodes'),
        'python/280.py': (NATIVE_280, 'the official entry previously returned a new list without modifying nums'),
        'javascript/280.js': (NATIVE_280, 'the official entry previously returned a new list without modifying nums'),
        'semantics/156-python.json': ('solve_effects, native_effects (mutates_inputs true), charged_costs and complexity; source_sha256 rebound', 'keep the semantics binding to the current source and its declared effects'),
        'semantics/156-javascript.json': ('solve_effects, native_effects (mutates_inputs true), charged_costs and complexity; source_sha256 rebound', 'keep the semantics binding to the current source and its declared effects'),
        'semantics/280-python.json': ('official_interface.in_place_arg 0, solve_effects, native_effects, charged_costs; source_sha256 rebound', 'keep the semantics binding to the current source and its declared effects'),
        'semantics/280-javascript.json': ('official_interface.in_place_arg 0, solve_effects, native_effects, charged_costs; source_sha256 rebound', 'keep the semantics binding to the current source and its declared effects'),
    },
    'requested-243-370-35-20261028-v1': {
        'cases.py': ('340 gains three non-BMP canary rows; expected values come from the unchanged ref_340', 'pin string_unit unicode_codepoint; two rows discriminate code points from UTF-16 code units'),
        'javascript/340.js': ('iterate Array.from(s) code points instead of UTF-16 code units', 'match Python str iteration and the oracle on non-BMP input (charged O(n) array)'),
        'semantics/340-python.json': ('string_unit unicode_codepoint, solve_effects, native_effects, charged_costs', 'declare the string unit the canary rows check'),
        'semantics/340-javascript.json': ('string_unit unicode_codepoint, solve_effects, native_effects, charged_costs and complexity; source_sha256 rebound', 'keep the semantics binding to the current source and its declared effects'),
    },
}
NATIVE_286 = ('Native-ABI split: wallsAndGates / Solution.wallsAndGates now rewrites rooms in place row by row and returns '
              'nothing (in_place_arg 0); solve still returns a new grid and leaves rooms unchanged.')
# Ordered revisions. For a changed file the latest revision naming it supplies the amendment text and date.
REVISIONS = [
    ('2026-11-02', REASONS),
    ('2026-11-02', {
        'requested-156-1940-31-20261028-v1': {
            'contracts.json': ('286 official_interface gains in_place_arg 0', 'declare the official in-place ABI so the runner judges rooms after the call'),
            'python/286.py': (NATIVE_286, 'the official entry previously returned a new grid without modifying rooms'),
            'javascript/286.js': (NATIVE_286, 'the official entry previously returned a new grid without modifying rooms'),
            'semantics/286-python.json': ('official_interface.in_place_arg 0, solve_effects, native_effects, charged_costs; source_sha256 rebound', 'keep the semantics binding to the current source and its declared effects'),
            'semantics/286-javascript.json': ('official_interface.in_place_arg 0, solve_effects, native_effects, charged_costs; source_sha256 rebound', 'keep the semantics binding to the current source and its declared effects'),
        },
    }),
]

NATIVE_369 = ('Native-ABI split: solve copies a native ListNode input (seen set rejects a cycle) so it neither mutates nor '
              'aliases caller nodes; plusOne / Solution.plusOne increments the caller list in place.')
NODE_DECLARATION = ('solve_effects (input mutation and output aliasing forbidden) and native_effects.mutates_inputs false; '
                    'source_sha256 unchanged', 'declare native node effects so check_native_abi.py exercises foreign node inputs')
NODE_FAMILY = {
    'requested-243-370-35-20261028-v1': [250, 270, 272, 298, 314, 333, 366],
    'requested-156-1940-31-20261028-v1': [742, 1214, 1740],
}
REVISIONS.append(('2026-11-02', {
    cohort: {f'semantics/{pid}-{lang}.json': NODE_DECLARATION for pid in ids for lang in ('python', 'javascript')}
    for cohort, ids in NODE_FAMILY.items()
}))
REVISIONS[-1][1]['requested-243-370-35-20261028-v1'].update({
    'python/369.py': (NATIVE_369, 'solve previously incremented a native ListNode input in place, returned caller nodes and looped forever on a cyclic list'),
    'javascript/369.js': (NATIVE_369, 'solve previously incremented a native ListNode input in place, returned caller nodes and looped forever on a cyclic list'),
    'semantics/369-python.json': ('solve_effects, native_effects (mutates_inputs true), charged_costs and complexity; source_sha256 rebound', 'keep the semantics binding to the current source and its declared effects'),
    'semantics/369-javascript.json': ('solve_effects, native_effects (mutates_inputs true), charged_costs and complexity; source_sha256 rebound', 'keep the semantics binding to the current source and its declared effects'),
})


def latest_reasons(cohort):
    merged = {}
    for at, table in REVISIONS:
        for path, text in table.get(cohort, {}).items():
            merged[path] = (at,) + text
    return merged


INVENTORY_REASON = {
    903: 'Reference and candidate I-step correction already recorded in pre-source-reference-freeze.json amendments (2026-10-29); source_inventory and authoring-catalog.json had kept the pre-fix hashes.',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def write_json(path, value, sort_keys=True):
    path.write_text(json.dumps(value, indent=2, sort_keys=sort_keys) + '\n')


def history_bytes(base, relative, digest):
    blob = base / 'study-history/blobs' / f'{digest}.bin'
    if blob.exists():
        return blob.read_bytes()
    rel = str((base / relative).relative_to(ROOT))
    for revision in subprocess.check_output(['git', 'log', '--format=%H', '--', rel], cwd=ROOT, text=True).split():
        shown = subprocess.run(['git', 'show', f'{revision}:{rel}'], cwd=ROOT, capture_output=True)
        if shown.returncode == 0 and sha(shown.stdout) == digest:
            return shown.stdout
    raise RuntimeError(f'Superseded bytes not recoverable: {rel} {digest}')


def archive(base, relative, digest):
    blob = base / 'study-history/blobs' / f'{digest}.bin'
    if not blob.exists():
        data = history_bytes(base, relative, digest)
        blob.parent.mkdir(parents=True, exist_ok=True)
        blob.write_bytes(data)
    return str(blob.relative_to(base))


def revise(cohort):
    base = AUTHORED / cohort
    manifest_path, freeze_path = base / 'manifest.json', base / 'pre-source-reference-freeze.json'
    manifest, freeze = json.loads(manifest_path.read_text()), json.loads(freeze_path.read_text())
    pinned = {f['path']: f['sha256'] for f in manifest['files']}
    amendments = freeze.setdefault('amendments', [])
    for path, (at, change, reason) in latest_reasons(cohort).items():
        old, new = pinned[path], sha((base / path).read_bytes())
        if old != new and not any(a['file'] == path and a['old_sha256'] == old and a['new_sha256'] == new for a in amendments):
            amendments.append({'file': path, 'after_candidates_existed': True, 'at': at, 'old_sha256': old,
                               'new_sha256': new, 'change': change, 'reason': reason})
    if 'current_sha256' in freeze:
        freeze['current_sha256'] = {p: sha((base / p).read_bytes()) for p in freeze['current_sha256']}
    write_json(freeze_path, freeze, sort_keys=False)

    catalog_path = base / 'authoring-catalog.json'
    catalog = json.loads(catalog_path.read_text())
    variants = {(v['problem_id'], v['language']): v for v in catalog['variants']}
    contracts = {p['id']: p for p in json.loads((base / 'contracts.json').read_text())['problems']}
    revised = []
    for row in manifest['source_inventory']:
        source = sha((base / row['path']).read_bytes())
        semantics = sha((base / row['semantics_path']).read_bytes())
        if (row['sha256'], row['semantics_sha256']) == (source, semantics):
            continue
        old_variant = variants[(row['id'], row['language'])]
        linked = [i for i, a in enumerate(amendments) if a['file'] in (row['path'], row['semantics_path'])
                  and a['old_sha256'] in (row['sha256'], row['semantics_sha256'])]
        entry = {'sha256': row['sha256'], 'semantics_sha256': row['semantics_sha256'],
                 'catalog_variant_id': old_variant['variant_id'], 'superseded_at': AT,
                 'freeze_amendments': ['pre-source-reference-freeze.json#/amendments/%d' % i for i in linked],
                 'bytes': {}}
        if row['sha256'] != source:
            entry['bytes']['source'] = archive(base, row['path'], row['sha256'])
        if row['semantics_sha256'] != semantics:
            entry['bytes']['semantics'] = archive(base, row['semantics_path'], row['semantics_sha256'])
        if row['id'] in INVENTORY_REASON:
            entry['reason'] = INVENTORY_REASON[row['id']]
        row.setdefault('supersedes', []).append(entry)
        row['sha256'], row['semantics_sha256'] = source, semantics
        revised.append(row)
    manifest['files'] = [{**f, 'sha256': sha((base / f['path']).read_bytes())} for f in manifest['files']]
    write_json(manifest_path, manifest)
    manifest_sha = sha(manifest_path.read_bytes())
    assignment_sha = sha((base / 'assignment.public-safe.json').read_bytes())

    for row in revised:
        key = (row['id'], row['language'])
        old = variants[key]
        record = {'language': row['language'], 'problem_id': row['id'],
                  'problem_contract_sha256': sha(compact(contracts[row['id']])),
                  'provenance': [{'assignment_sha256': assignment_sha, 'manifest_sha256': manifest_sha,
                                  'semantics_path': row['semantics_path'], 'source_path': row['path']}],
                  'qualification': old['qualification'], 'semantics_sha256': row['semantics_sha256'],
                  'source_sha256': row['sha256']}
        record['variant_id'] = sha(compact(record))
        record['supersedes'] = old.get('supersedes', []) + [{k: v for k, v in old.items() if k != 'supersedes'}]
        index = catalog['index'][str(row['id'])][row['language']]
        index[index.index(old['variant_id'])] = record['variant_id']
        variants[key] = record
        print(cohort, row['path'], old['variant_id'][:12], '->', record['variant_id'][:12])
    catalog['variants'] = [variants[(v['problem_id'], v['language'])] for v in catalog['variants']]
    if revised:
        catalog['variant_id_rules'] = {
            'original': 'Generator not recorded in this repository; prior variant IDs are retained verbatim under supersedes.',
            'revised': 'sha256 of json.dumps(record without variant_id and supersedes, sort_keys=True, separators=(",", ":"))',
        }
    write_json(catalog_path, catalog)

    sums = base / 'SHA256SUMS'
    paths = [line.split('  ', 1)[1] for line in sums.read_text().splitlines()]
    sums.write_text(''.join(f'{sha((base / p).read_bytes())}  {p}\n' for p in paths))


if __name__ == '__main__':
    for name in REASONS:
        revise(name)
