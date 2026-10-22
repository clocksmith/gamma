"""Read-only admission inventory for the M1 500-problem population (ledger revision 1810).

Rebuilds the 363 metadata-eligible JavaScript problems from their three stated sources
(complete JavaScript entries in the revision-1810 ledger checkpoint, the qualified
development catalogs and the current 150 development problems), excludes the protected
reservation, and records for every problem beyond the 150 which source, receipt, test and
contract checks already pass and what it still needs. Writes nothing outside --output.
No ledger, claim or catalog is changed.
"""
import argparse, collections, gzip, hashlib, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = HERE.parents[1]  # projects/algorithm_solver
TASK = Path('/home/x/Documents/Codex/2026-10-19/task')
LEDGER = TASK / 'corpus-campaign-v1/checkpoints/revision-1810-v16/ledger.json.gz'
LEDGER_SHA = '7a1cdcc6c0a3a31d21d140f147faefa2ac75193449de880b9b721dc6cc08d1ca'
STAGE150 = TASK / 'literal-scale150-v1/stage-freeze.json'
CATALOGS = [f'javascript_development_catalog_v{i}' for i in (1, 2, 3, 4)] + [f'bilingual_development_catalog_v{i}' for i in (2, 3, 4)]
RESERVATION = P / 'contracts/typed_confirmation_v1.json'
# Encodings the literal harness (scale150-v1 harness.cjs) decodes and encodes today.
HARNESS_KEYS = {'__list_node__', '__tree_node__', '__gamma_bigint_v1__'}
# Comparison modes the judge's _matches accepts in earlier literal stages.
COMPARE_OK = {'return', 'return:unordered_outer'}
sha = lambda b: hashlib.sha256(b).hexdigest()


def test_hash_forms(raw):
    part = json.loads(raw)
    return part, {sha(raw), sha(json.dumps(part, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()),
                  sha(json.dumps(part, sort_keys=True, ensure_ascii=False).encode()),
                  sha(json.dumps(part, sort_keys=True, separators=(',', ':')).encode())}


def special_keys(x, out):
    if isinstance(x, list):
        for v in x: special_keys(v, out)
    elif isinstance(x, dict):
        for k, v in x.items():
            if k.startswith('__'): out.add(k)
            special_keys(v, out)


def artifact(ref):
    """Return (bytes or None, hash_ok) for a ledger artifact reference."""
    p = Path(ref['path'])
    if not p.exists(): return None, False
    b = p.read_bytes()
    return b, sha(b) == ref['sha256']


def check_tests(sets):
    out = {'files_present': True, 'hashes_match': True, 'count_matches': True, 'cases': 0,
           'shape_ok': True, 'compare_modes': set(), 'encodings': set()}
    for s in sets:
        p = P / 'data/derived' / s['path']
        if not p.exists():
            out['files_present'] = False; continue
        part, forms = test_hash_forms(p.read_bytes())
        out['hashes_match'] &= s['sha256'] in forms
        out['count_matches'] &= len(part) == s['tests']
        out['cases'] += len(part)
        for t in part:
            out['shape_ok'] &= isinstance(t, dict) and set(t) <= {'args', 'expected', 'compare'}
            out['compare_modes'].add(t.get('compare', 'return'))
            special_keys([t.get('args'), t.get('expected')], out['encodings'])
    out['compare_modes'] = sorted(out['compare_modes']); out['encodings'] = sorted(out['encodings'])
    return out


def source_traits(src):
    defined = set(re.findall(r'\bclass\s+([A-Za-z_$][\w$]*)', src)) | set(re.findall(r'\bfunction\s+([A-Z][\w$]*)\s*\(', src))
    used = set(re.findall(r'\bnew\s+([A-Z][\w$]*)\s*\(', src))
    builtin = {'Array', 'Map', 'Set', 'Int32Array', 'Uint8Array', 'Int8Array', 'Uint16Array', 'Int16Array', 'Uint32Array',
               'Float64Array', 'Float32Array', 'BigInt64Array', 'BigUint64Array', 'Error', 'WeakMap', 'WeakSet', 'Date',
               'RegExp', 'Object', 'Uint8ClampedArray', 'ArrayBuffer', 'DataView', 'Proxy', 'Promise', 'TypeError', 'RangeError'}
    return {'bytes': len(src.encode()), 'external_constructors': sorted(used - defined - builtin),
            'defines_classes': sorted(defined)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--output', type=Path, required=True); a = ap.parse_args()
    raw = gzip.open(LEDGER).read(); assert sha(raw) == LEDGER_SHA, 'ledger checkpoint is not revision 1810'
    ledger = json.loads(raw); assert ledger['revision'] == 1810
    E = ledger['entries']
    probs = {}
    for line in (P / 'data/derived/problems.jsonl').open():
        d = json.loads(line); probs[d['uid']] = d
    res = json.loads(RESERVATION.read_text())['reservation']
    protected_ids, protected_families, protected_uids = set(), set(), set()
    for r in res['pool']:
        protected_families.add(r['family'])
        for m in r['members']:
            protected_uids.add(m)
            protected_ids.add(int(m.split(':')[1]))
    stage = json.loads(STAGE150.read_text())
    dev = set(stage['prior_ids']) | set(stage['additional_ids']); assert len(dev) == 150
    js_complete = {v['id']: v for v in E.values() if v['language'] == 'javascript' and v['status'] == 'complete'}
    catalog_rows = {}
    for name in CATALOGS:
        c = json.loads((P / f'data/derived/{name}.json').read_text())
        for r in c['rows']:
            impl = next((i for i in r.get('implementations', []) if i['language'] == 'javascript' and i.get('qualified')), None)
            if impl: catalog_rows.setdefault(r['id'], (name, r, impl))
    union = (set(js_complete) | set(catalog_rows) | dev) - protected_ids
    assert len(union) == 363 and len(union - dev) == 213, (len(union), len(union - dev))
    near = json.loads((P / 'data/derived/near_duplicates.json').read_text())
    near_keys = collections.defaultdict(set)  # key -> paired uids
    for pr in near['pairs']:
        near_keys[pr['index_key']].add(pr['pool_uid'])
    population_uids = {f'lcd:{i}' for i in union}

    rows = []
    for pid in sorted(union - dev):
        uid = f'lcd:{pid}'; meta = probs.get(uid, {})
        row = {'id': pid, 'uid': uid, 'difficulty': meta.get('difficulty'), 'io_mode': meta.get('io_mode'),
               'license': meta.get('license'), 'checks': {}, 'needs': []}
        ck = row['checks']
        e = js_complete.get(pid)
        if e is not None:
            row.update(route='ledger-1810-complete', key=e['key'], family=e['family'])
            att = e['attempts'][-1]
            src, ok = artifact(e['normalized']); ck['source_present'] = src is not None; ck['source_hash'] = ok
            row['source_sha256'] = e['normalized']['sha256']
            rec = {r['kind']: r['receipt'] for r in att['receipts']}
            ex_b, ex_ok = artifact(rec['execution']) if 'execution' in rec else (None, False)
            ck['execution_receipt_hash'] = ex_ok
            if ex_b:
                ex = json.loads(ex_b)
                ck['execution_receipt_passed'] = (ex['status'] == 'passed' and ex['independent_total'] > 0
                    and ex['independent_passed'] == ex['independent_total'] and ex['public_passed'] == ex['public_total']
                    and ex.get('mutation_passed') is True and ex.get('alias_passed') is True and ex.get('sandboxed') is True
                    and ex.get('expected_outputs_in_sandbox') is False and ex.get('infrastructure_errors') == 0
                    and ex['normalized_sha256'] == e['normalized']['sha256'])
                row['receipt_independent_passed'] = ex['independent_passed']
            for kind in ('standard', 'review'):
                ck[f'{kind}_receipt_hash'] = artifact(rec[kind])[1] if kind in rec else False
            con_b, con_ok = artifact(att['contract']); ck['contract_hash'] = con_ok
            if con_b:
                con = json.loads(con_b)
                row['contract'] = {k: con.get(k) for k in ('comparison', 'interface', 'mutation_contract', 'alias_contract')}
                ec = con.get('entry_contract')
                if ec:
                    ck['entry_contract_hash'] = Path(ec['path']).exists() and sha(Path(ec['path']).read_bytes()) == ec['sha256']
            sets = e['independent_sets']
        else:
            name, r, impl = catalog_rows[pid]
            row.update(route=f'catalog:{name}', key=r['key'], family=r.get('family') or r['key'].split(':', 1)[1])
            p = P / impl['source']; src = p.read_bytes() if p.exists() else None
            ck['source_present'] = src is not None; ck['source_hash'] = bool(src) and sha(src) == impl['source_sha256']
            row['source_sha256'] = impl['source_sha256']
            rp = P / impl['qualification_receipt']
            if impl.get('evidence_run') == 'source-corpus-js-py-128-v2':
                # Five-family foundation: bound by its source seal, as scale100-v1 did for 1512.
                seal_path = P / 'runs/source-corpus-js-py-128-v2/source-seal.json'
                seal = next(x for x in json.loads(seal_path.read_text()) if x['uid'] == uid)
                ck['execution_receipt_hash'] = seal['sources']['javascript-normalized']['sha256'] == impl['source_sha256']
                ck['execution_receipt_passed'] = str(impl['qualified']) == 'True'
                sets = [{'uid': uid, 'tests': int(impl['independent_cases']), 'sha256': seal['independent_tests_sha256'], 'path': f'tests/lcd__{pid}.json'}]
                row['route'] += '+five-family-seal'
            elif rp.exists():
                rb = rp.read_bytes(); rj = json.loads(rb)
                ck['execution_receipt_hash'] = not impl.get('qualification_receipt_sha256') or sha(rb) == impl['qualification_receipt_sha256']
                ck['execution_receipt_passed'] = bool(rj.get('qualified', impl['qualified']))
                sets = [{'uid': uid, 'tests': impl['independent_cases'], 'sha256': m['sha256'],
                         'path': str(Path(m['absolute_path']).relative_to(P / 'data/derived')) if str(m.get('absolute_path', '')).startswith(str(P / 'data/derived')) else m.get('path', '')}
                        for m in rj.get('independent_test_sets', rj.get('test_metadata', []))]
            else:
                ck['execution_receipt_hash'] = False; ck['execution_receipt_passed'] = False; sets = []
            ck['contract_hash'] = bool(impl.get('evaluation_contract')) or row['route'].endswith('five-family-seal')
        tests = check_tests(sets) if sets else {'files_present': False, 'hashes_match': False, 'count_matches': False,
                                                'cases': 0, 'shape_ok': False, 'compare_modes': [], 'encodings': []}
        ck['tests_present'] = tests['files_present'] and bool(sets); ck['tests_hash'] = tests['hashes_match']
        ck['tests_count'] = tests['count_matches']; ck['tests_shape'] = tests['shape_ok']
        row['independent_cases'] = tests['cases']; row['compare_modes'] = tests['compare_modes']; row['encodings'] = tests['encodings']
        ck['protected_id_clear'] = pid not in protected_ids
        ck['protected_family_clear'] = row['family'] not in protected_families
        paired = near_keys.get(row['key'], set())
        ck['protected_near_duplicate_clear'] = not (paired & protected_uids)
        row['near_duplicates_in_population'] = sorted(paired & (population_uids - {uid}))
        traits = source_traits(src.decode()) if src else {'bytes': None, 'external_constructors': [], 'defines_classes': []}
        method = None
        try: method = (eval(meta['entry']) if isinstance(meta.get('entry'), str) else meta.get('entry') or {}).get('method')
        except Exception: pass
        text = src.decode() if src else ''
        row['entry_method'] = method
        if re.search(r'class\s+Solution\s*\{', text) and method and re.search(r'\b' + re.escape(method) + r'\s*\(', text):
            row['entry_form'] = 'class Solution method'
        elif re.search(r'\bfunction\s+solve\s*\(', text):
            row['entry_form'] = 'function solve'
        elif method and re.search(r'\b(function\s+|var\s+|const\s+|let\s+)' + re.escape(method) + r'\b', text):
            row['entry_form'] = 'named function'
        else:
            row['entry_form'] = None
        row['source_bytes'] = traits['bytes']; row['external_constructors'] = traits['external_constructors']
        # What the literal stage still has to establish or supply.
        if not (ck['source_present'] and ck['source_hash']): row['needs'].append('source: missing or hash mismatch')
        if not ck.get('execution_receipt_hash') or not ck.get('execution_receipt_passed'): row['needs'].append('receipt: execution receipt missing, mismatched or not fully passed')
        for kind in ('standard_receipt_hash', 'review_receipt_hash', 'contract_hash', 'entry_contract_hash'):
            if kind in ck and not ck[kind]: row['needs'].append(f'receipt: {kind.removesuffix("_hash")} missing or mismatched')
        if not (ck['tests_present'] and ck['tests_hash'] and ck['tests_count'] and ck['tests_shape']): row['needs'].append('tests: independent set missing, mismatched or malformed')
        if not (ck['protected_id_clear'] and ck['protected_family_clear'] and ck['protected_near_duplicate_clear']): row['needs'].append('exclude: protected id, family or near duplicate')
        if row['near_duplicates_in_population']: row['needs'].append('dedupe: near duplicate of another population problem; keep one')
        unsupported = [m for m in tests['compare_modes'] if m not in COMPARE_OK]
        if unsupported: row['needs'].append('adapter: comparison mode ' + ', '.join(unsupported))
        enc = [k for k in tests['encodings'] if k not in HARNESS_KEYS]
        if enc: row['needs'].append('adapter: test encoding ' + ', '.join(enc))
        if traits['external_constructors']: row['needs'].append('packaging: append and charge constructor source for ' + ', '.join(traits['external_constructors']))
        if not row['entry_form']: row['needs'].append('interface: entry point not found in source')
        row['needs'].append('literal qualification: original oracle plus result/type, mutation and alias parity in the frozen stage harness')
        row['ready_for_stage_qualification'] = all(n.startswith('literal qualification') or n.startswith('packaging') for n in row['needs'])
        rows.append(row)

    # Distinctness across the whole 363: repeated key, family or source hash.
    dev_rows = {}
    for pid in dev:
        e = js_complete.get(pid)
        if e is not None: dev_rows[pid] = (e['key'], e['family'], e['normalized']['sha256'])
        elif pid in catalog_rows:
            _, r, impl = catalog_rows[pid]; dev_rows[pid] = (r['key'], r.get('family') or r['key'].split(':', 1)[1], impl['source_sha256'])
    seen = collections.defaultdict(list)
    for pid, (k, f, h) in dev_rows.items():
        seen[('key', k)].append(pid); seen[('family', f)].append(pid); seen[('source', h)].append(pid)
    for r in rows:
        for t in (('key', r['key']), ('family', r['family']), ('source', r['source_sha256'])): seen[t].append(r['id'])
    duplicates = {f'{t[0]}:{t[1]}': sorted(v) for t, v in seen.items() if len(v) > 1}
    for r in rows:
        clash = sorted({x for t, v in seen.items() if len(v) > 1 and r['id'] in v and t[0] in ('key', 'source') for x in v} - {r['id']})
        r['duplicates_in_population'] = clash
        if clash: r['needs'].insert(-1, 'dedupe: same key or identical source as another population problem')
        r['ready_for_stage_qualification'] = all(n.startswith('literal qualification') or n.startswith('packaging') for n in r['needs'])
    unresolved_dev = sorted(dev - set(dev_rows))
    summary = {
        'schema': 'gamma.literal-admission-inventory.v2',
        'ledger_revision': 1810, 'ledger_sha256': LEDGER_SHA,
        'available_metadata_union': len(union), 'current_development_count': len(dev),
        'candidates_beyond_150': len(rows),
        'by_route': dict(collections.Counter(r['route'] for r in rows)),
        'by_difficulty': dict(collections.Counter(r['difficulty'] for r in rows)),
        'ready_for_stage_qualification': sum(r['ready_for_stage_qualification'] for r in rows),
        'needs_count': dict(collections.Counter(n.split(':')[0] for r in rows for n in r['needs'])),
        'needs_detail': dict(collections.Counter(n for r in rows for n in r['needs'])),
        'population_duplicates': duplicates, 'development_rows_unresolved': unresolved_dev,
        'gap_to_500_if_all_pass': 500 - len(union),
        'protected': {'ids': len(protected_ids), 'families': len(protected_families), 'opened': False},
        'caveat': 'Read-only metadata and receipt checks. No candidate source or case content was published; literal-stage qualification has not run. Passing these checks admits a problem to stage qualification only.',
        'script_sha256': sha(Path(__file__).read_bytes()),
    }
    a.output.mkdir(parents=True, exist_ok=True)
    (a.output / 'admission-inventory.json').write_text(json.dumps({'summary': summary, 'rows': rows}, indent=1, sort_keys=True) + '\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
