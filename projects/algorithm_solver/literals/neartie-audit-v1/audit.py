"""neartie-audit-v1: do the two single-character-fraction near-misses survive a tie-break-only encoder? (FREEZE.md)

  audit.py --work DIR --output DIR/neartie-audit/run-v1

Fixed artifacts only (no fitting, no rewriting, no case execution): item 10 compiler-choice joint-128 against its
searched control-128, and item 14 coupled_joint-256 / coupled-256 against the item 13 seed (incremental successor
rule) and against control-256. Every arm is encoded with segmentation-audit-v1's `canonical` and
`shortest_min_char` policies (segment.py, pinned). Canonical must reproduce the recorded per-problem counts exactly.
Predicates are then recomputed under historical (both canonical), matched (both shortest_min_char) and mixed
(candidate shortest_min_char, comparator canonical) encoder pairings. Recorded verdicts are not changed.
"""
import argparse, hashlib, json, statistics, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sys.path[:0] = [str(LIT / 'segmentation-audit-v1'), str(LIT / 'cost-decomposition-v1')]
import segment, analyze

sha = lambda raw: hashlib.sha256(raw).hexdigest()
POLICIES = ('canonical', 'shortest_min_char')


def contract():
    c = json.loads((HERE / 'contract.json').read_text())
    for rel, h in c['code_hashes'].items(): assert sha((LIT / rel).read_bytes()) == h, rel
    return c


def encode_arm(work, arm, evidence, val_ids):
    folder = work / arm['relative_path']
    for name in ('sources.json', 'dictionary.json'):
        assert sha((folder / name).read_bytes()) == arm['private_sha256'][name], (arm['name'], name)
    texts = json.loads((folder / 'sources.json').read_text()); vocab = json.loads((folder / 'dictionary.json').read_text())
    record = next(a for a in evidence['arms'] if a['arm'] == arm['arm'] and a['width'] == arm['width'])
    assert all(record['qualification'][str(p)]['passed'] for p in val_ids) and not record['illegal_entry_sha256']
    db = analyze.dictionary_bytes(vocab); out = {}
    for policy in POLICIES:
        rows = {}
        for pid in val_ids:
            text = texts[str(pid)]; prior = record['per_problem'][str(pid)]
            assert sha(text.encode()) == prior['source_sha256']
            seq = segment.encode(text, vocab, policy); packet = analyze.encode(vocab, seq, arm['width'])
            assert analyze.decode(db, packet) == text
            single = sum(len(vocab[i]) == 1 for i in seq)
            if policy == 'canonical':
                assert seq == analyze.shortest_encode(text, vocab)
                assert (len(seq), single) == (prior['selections'], prior['single_characters']), (arm['name'], pid)
            rows[str(pid)] = {'selections': len(seq), 'actions': len(seq) + 1, 'single_characters': single, 'packet_bytes': len(packet)}
        out[policy] = rows
    return out, len(db)


def summary(rows, db):
    acts = sorted(r['actions'] for r in rows.values()); sel = sum(r['selections'] for r in rows.values())
    return {'actions': sum(acts), 'median': statistics.median(acts), 'p90': acts[-(-9 * len(acts) // 10) - 1],
            'single_character_codes': sum(r['single_characters'] for r in rows.values()),
            'single_character_fraction': sum(r['single_characters'] for r in rows.values()) / sel,
            'package_bytes': db + sum(r['packet_bytes'] for r in rows.values())}


def paired(a, b):
    d = [a[p]['actions'] - b[p]['actions'] for p in a]
    return {'better': sum(x < 0 for x in d), 'same': sum(x == 0 for x in d), 'worse': sum(x > 0 for x in d)}


def readiness(cand, comp, pc, rule):
    """The frozen input-candidate rule of items 10/13/14 against a comparator (decode/qualification/audit checked above)."""
    if rule == 'ready':
        return {'actions_5pct': cand['actions'] <= 0.95 * comp['actions'], 'median_lower': cand['median'] < comp['median'],
                'p90_lower': cand['p90'] < comp['p90'], 'improved_60': pc['better'] >= 60, 'worsened_25': pc['worse'] <= 25,
                'fraction_not_higher': cand['single_character_fraction'] <= comp['single_character_fraction'],
                'package_105': cand['package_bytes'] <= 1.05 * comp['package_bytes']}
    return {'fewer_actions': cand['actions'] < comp['actions'], 'median_not_worse': cand['median'] <= comp['median'],
            'p90_not_worse': cand['p90'] <= comp['p90'], 'fraction_not_higher': cand['single_character_fraction'] <= comp['single_character_fraction'],
            'package_105': cand['package_bytes'] <= 1.05 * comp['package_bytes'], 'worsened_25': pc['worse'] <= 25}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args(); c = contract(); a.output.mkdir(parents=True, exist_ok=False)
    val_ids = json.loads((LIT / 'cost-decomposition-v1/contract.json').read_text())['partition']['dev_val']
    encoded, sums = {}, {}
    for arm in c['arms']:
        evidence = json.loads((LIT / arm['evidence']).read_text())
        assert sha((LIT / arm['evidence']).read_bytes()) == arm['evidence_sha256']
        rows, db = encode_arm(a.work.resolve(), arm, evidence, val_ids)
        encoded[arm['name']] = rows
        sums[arm['name']] = {p: summary(rows[p], db) for p in POLICIES}
    comparisons = []
    for comp in c['comparisons']:
        for pairing, (pc_, pk_) in (('historical', ('canonical', 'canonical')), ('matched', ('shortest_min_char', 'shortest_min_char')),
                                    ('mixed', ('shortest_min_char', 'canonical'))):
            cand, base = sums[comp['candidate']][pc_], sums[comp['comparator']][pk_]
            pr = paired(encoded[comp['candidate']][pc_], encoded[comp['comparator']][pk_])
            checks = readiness(cand, base, pr, comp['rule'])
            if pairing == 'historical':  # must reproduce exactly the recorded failing predicates
                assert sorted(k for k, v in checks.items() if not v) == sorted(comp['expected_historical_failed']), comp['label']
            comparisons.append({**comp, 'pairing': pairing, 'candidate_policy': pc_, 'comparator_policy': pk_,
                                'candidate': cand, 'comparator_summary': base, 'paired': pr, 'checks': checks, 'passes': all(checks.values())})
    out = {'schema': 'gamma.neartie-audit-v1.results.v1', 'contract_sha256': sha((HERE / 'contract.json').read_bytes()),
           'arms': sums, 'comparisons': comparisons, 'decodes': sum(len(r[p]) for r in encoded.values() for p in POLICIES)}
    (a.output / 'results.json').write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
    for x in comparisons:
        print(f"{x['label']:28} {x['pairing']:10} passes={x['passes']} failed={[k for k, v in x['checks'].items() if not v]} "
              f"frac {x['candidate']['single_character_fraction']:.4f} vs {x['comparator_summary']['single_character_fraction']:.4f}")


if __name__ == '__main__':
    main()
