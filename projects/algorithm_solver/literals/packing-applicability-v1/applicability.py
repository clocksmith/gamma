"""packing-applicability-v1 (board item 76): does item 71's packing count ever bind on the original fit sources? (FREEZE.md)

  applicability.py --work DIR      prints and writes evidence/results.json (aggregates and hashes only)

Item 71 replaces an entry's occurrence count m_ep in source p by n_ep = min(m_ep, floor(N_p / len(e))). n_ep < m_ep holds iff
m_ep * len(e) > N_p. binding() counts, over EVERY substring e of length >= 2 of every fit source p (a superset of the allowed class:
bans and ownership only remove entries), the (p, e) pairs with m_ep * len(e) > N_p, counting overlapping occurrences in m_ep. If the
count is 0 in a cohort, n = m for every entry, owner or shared, and item 71's owner and global refinements equal items 63/66 there.
"""
import argparse, hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sha = lambda raw: hashlib.sha256(raw).hexdigest()
COHORTS = {'R': ('binding-descent/run-v1/control-256/fit-sources.json', 'c0a4b1b5f365c75e88f7653c95b7e2fdce6be2c2c6d998c0305e07a0ccb92b82', 76107),
           'naming': ('binding-descent/run-v1/scope_joint-256/fit-sources.json', '4785b837f53a4798a9005e49d33d9d8e1795d7c83a597d2bc1b133680fbe7063', 76033)}


def binding(text):
    """(pairs with m*len > N, the largest m*len/N over substrings of length >= 2) for one source; m counts overlapping occurrences."""
    N = len(text); pairs = 0; worst = 0.0
    for length in range(2, N + 1):
        counts = {}
        for i in range(N - length + 1):
            s = text[i:i + length]; counts[s] = counts.get(s, 0) + 1
        top = max(counts.values())
        worst = max(worst, top * length / N)
        if top * length <= N: continue  # every substring of this length has m*len <= N
        pairs += sum(m * length > N for m in counts.values())
    return pairs, worst


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); a = ap.parse_args()
    out = {'schema': 'gamma.packing-applicability-v1.evidence.v1', 'cohorts': {}}
    for cohort, (rel, digest, chars) in COHORTS.items():
        raw = (a.work / rel).read_bytes(); assert sha(raw) == digest, rel
        texts = json.loads(raw); assert len(texts) == 300 and sum(map(len, texts.values())) == chars  # item 63's full_shape
        per = {p: binding(t) for p, t in texts.items()}
        out['cohorts'][cohort] = {'sources': len(texts), 'source_characters': chars, 'fit_sources_sha256': digest,
                                  'binding_pairs': sum(x[0] for x in per.values()), 'sources_with_binding_pairs': sum(x[0] > 0 for x in per.values()),
                                  'max_m_len_over_N': max(x[1] for x in per.values())}
    out['packing_never_binds'] = all(v['binding_pairs'] == 0 for v in out['cohorts'].values())
    (HERE / 'evidence').mkdir(exist_ok=True); (HERE / 'evidence/results.json').write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
