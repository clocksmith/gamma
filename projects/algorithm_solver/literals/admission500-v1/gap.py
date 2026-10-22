"""Freeze the selection rule and order for the 137 newly written problems (gap to 500).

Eligible: JavaScript entries pending at both ledger revision 1810 and the current read-only
ledger snapshot, unclaimed, unreserved, functional, outside the protected reservation (ID and
family), outside the 363 and their families, with a hash-valid independent set of at least 20
cases. Quotas follow the 363's difficulty mix. Order within a stratum is sha256(SEED + uid),
fixed before any solution is written. Writes gap-selection.json; reads no source or case content
beyond hashing the case files.
"""
import argparse, collections, gzip, hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from inventory import LEDGER, LEDGER_SHA, P, RESERVATION, STAGE150, test_hash_forms

SEED = 'gamma-admission500-gap-v1'
CURRENT = Path('/home/x/Documents/Codex/2026-10-19/task/corpus-campaign-v1/ledger.json')
sha = lambda b: hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--output', type=Path, required=True); a = ap.parse_args()
    raw = gzip.open(LEDGER).read(); assert sha(raw) == LEDGER_SHA; A = json.loads(raw)['entries']
    cur_raw = CURRENT.read_bytes(); cur = json.loads(cur_raw); B = cur['entries']
    probs = {json.loads(l)['uid']: json.loads(l) for l in (P / 'data/derived/problems.jsonl').open()}
    res = json.loads(RESERVATION.read_text())['reservation']
    prot_ids = {int(m.split(':')[1]) for r in res['pool'] for m in r['members']}; prot_fam = {r['family'] for r in res['pool']}
    inv = json.loads((HERE / 'evidence/admission-inventory.json').read_text())
    st = json.loads(STAGE150.read_text()); dev = set(st['prior_ids']) | set(st['additional_ids'])
    population = dev | {r['id'] for r in inv['rows']}; assert len(population) == 363
    pop_fam = {A[f'{i:04d}:javascript']['family'] for i in population if f'{i:04d}:javascript' in A} | {r['family'] for r in inv['rows']}
    mix = collections.Counter(probs[f'lcd:{i}']['difficulty'] for i in population)
    quota = {d: round(137 * n / 363) for d, n in mix.items()}
    quota[max(quota, key=quota.get)] += 137 - sum(quota.values())
    pool, excluded = collections.defaultdict(list), collections.Counter()
    for k, v in B.items():
        if v['language'] != 'javascript': continue
        a0 = A.get(k)
        if v['status'] != 'pending' or not a0 or a0['status'] != 'pending': excluded['not pending at both revisions'] += 1; continue
        if v.get('claim') or a0.get('claim'): excluded['claimed'] += 1; continue
        if (v['reservation'] or {}).get('owner'): excluded['reserved'] += 1; continue
        if v['id'] in prot_ids or v['family'] in prot_fam: excluded['protected id or family'] += 1; continue
        if v['id'] in population: excluded['in the 363'] += 1; continue
        if v['family'] in pop_fam: excluded['shares a family with the 363'] += 1; continue
        m = probs.get(f"lcd:{v['id']}")
        if not m or m.get('io_mode') != 'functional': excluded['not functional'] += 1; continue
        ok = bool(v['independent_sets'])
        for s in v['independent_sets']:
            p = P / 'data/derived' / s['path']
            if not p.exists(): ok = False; break
            part, forms = test_hash_forms(p.read_bytes()); ok &= s['sha256'] in forms and len(part) == s['tests'] >= 20
        if not ok: excluded['independent set missing, mismatched or under 20 cases'] += 1; continue
        uid = f"lcd:{v['id']}"
        pool[m['difficulty']].append({'id': v['id'], 'uid': uid, 'key': v['key'], 'family': v['family'], 'difficulty': m['difficulty'],
                                      'independent_sets': v['independent_sets'], 'order_key': sha((SEED + uid).encode())})
    order = {d: sorted(rows, key=lambda r: r['order_key']) for d, rows in pool.items()}
    out = {'schema': 'gamma.literal-admission500-gap-selection.v1', 'seed': SEED, 'quota': quota, 'population_mix': dict(mix),
           'ledger_1810_sha256': LEDGER_SHA, 'current_ledger_revision': cur['revision'], 'current_ledger_sha256': sha(cur_raw),
           'excluded': dict(excluded), 'pool_size': {d: len(r) for d, r in order.items()},
           'selected': {d: [r['id'] for r in order[d][:q]] for d, q in quota.items()},
           'replacement_order': {d: [r['id'] for r in order[d][quota[d]:quota[d] + 3 * quota[d]]] for d in quota},
           'rows': {str(r['id']): {k: r[k] for k in ('uid', 'key', 'family', 'difficulty', 'independent_sets')}
                    for d in quota for r in order[d][:4 * quota[d]]},
           'script_sha256': sha(Path(__file__).read_bytes())}
    a.output.write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
    print(json.dumps({k: out[k] for k in ('quota', 'population_mix', 'excluded', 'pool_size', 'current_ledger_revision')}))


if __name__ == '__main__':
    main()
