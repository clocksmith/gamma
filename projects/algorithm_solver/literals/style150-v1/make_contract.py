"""Write contract.json and the rewriter packets for style150-v1 (refuses to overwrite the contract)."""
import hashlib, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent; P = LIT.parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(LIT / 'admission500-v1'))
sha = lambda b: hashlib.sha256(b).hexdigest()
W = Path('/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1')
REFINE = Path('/home/x/Documents/Codex/2026-10-19/task/literal-scale150-refine-v1/measurement')
SEED = 'style150-v1-heldout'


def designed_forms():
    """Exact strings from STYLE.md's loop heads and preferred-forms table."""
    text = (HERE / 'STYLE.md').read_text()
    section = text[text.index('8. Loops use exactly these heads'):text.index('10. Use `n`')]
    forms = []
    for code in re.findall(r'`([^`]+)`', section):
        code = code.replace('\\|', '|')
        if len(code) >= 3 and '...' not in code and code not in forms: forms.append(code)
    return forms


def main():
    import style
    out = HERE / 'contract.json'; assert not out.exists()
    rows = style.population(W); ss, meta = style.load_pool()
    ids = sorted(rows)
    order = sorted(ids, key=lambda i: sha(f'{SEED}{i}'.encode()))
    heldout, train = sorted(order[:30]), sorted(order[30:])
    req = W / 'style150/pool/requalification.json'
    probs = {json.loads(l)['uid']: json.loads(l) for l in (P / 'data/derived/problems.jsonl').open()}
    best = json.loads((REFINE / 'token-input-256/manifest.json').read_text())
    chosen = {int(p['id']): p for p in best['programs']}
    pk = W / 'style150/packets'; pk.mkdir(parents=True, exist_ok=True)
    for pid in ids:
        d = pk / str(pid); d.mkdir(exist_ok=True)
        (d / 'original.js').write_bytes((W / 'population' / f'{pid}.js').read_bytes())
        bv = chosen[pid]['variant']; (d / 'best-existing.js').write_text(ss[pid][bv])
        m = probs[f'lcd:{pid}']
        (d / 'problem.md').write_text(f"# {pid}. {m['title']} ({m['difficulty']})\n\n{m['statement']}\n\n"
                                      f"Original entry: `{rows[pid]['entry']}`. The rewrite is called as `solve(...)` with the same arguments in the same order.\n")
    starts = {str(s): str(REFINE / f'token-input-{s}/dictionary.json') for s in (128, 256)}
    code = ['style150-v1/style.py', 'style150-v1/measure.py', 'style150-v1/make_contract.py', 'style150-v1/STYLE.md',
            'matched80-v3/run.py', 'matched80-v1/run.py', 'joint-v1/search.py', 'scale-v2/search.py',
            'admission500-v1/stage.py', 'admission500-v1/qualify_rules.py', 'admission500-v1/harness.cjs',
            'admission500-v1/harness-exact-integer.cjs', 'admission500-v1/population.py']
    c = {'schema': 'gamma.style150-v1.contract.v1',
         'goal': 'v2:2b joint source and dictionary optimization (M1 allows offline source rewriting); compression-first literal policy',
         'population': 'The first 150 development problems (scale150-v1 IDs), exposed development data, corpus cases from admission500-v1 population.py.',
         'ids': ids, 'split': {'seed': SEED, 'rule': 'sha256(seed + id) ascending; first 30 held out', 'heldout': heldout, 'train': train},
         'inputs': {'population_manifest_sha256': sha((W / 'population/manifest.json').read_bytes()),
                    'population_baseline_sha256': sha((W / 'population-baseline/report.json').read_bytes()),
                    'pool_requalification_sha256': sha(req.read_bytes()),
                    'start_dictionaries': starts,
                    'start_dictionary_sha256': {k: sha(Path(v).read_bytes()) for k, v in starts.items()},
                    'style_sha256': sha((HERE / 'STYLE.md').read_bytes())},
         'pool': 'S1: the 998 of 1,006 scale150 alternatives that pass the corpus cases with strict parity (8 legacy-shared variants of 169 and 961 fail and are excluded everywhere). S0: each problem\'s original. S2: S1 plus each qualified rewrite. SE: the rewrite where qualified, else the original.',
         'rewrites': {'count': 'one per problem, by rewriter agents following STYLE.md', 'inputs': 'original, the best existing compact variant and the statement; no dictionary, encoding or measurement output',
                      'checks_per_problem': style.CHECK_LIMIT, 'qualification': 'all corpus cases: unchanged return oracle plus strict parity with the original observation (result, type, arguments after, alias edges)',
                      'failure': 'a rewrite that fails qualification is recorded and not replaced; that problem has no style source'},
         'designed_forms': designed_forms(),
         'search': {'method': 'matched80-v3 local_search with hybrid_proposer (3/4 joint-v1 span order, 1/4 designed forms)',
                    'neighborhood': {'additions': 96, 'designed_fraction': 0.25, 'swaps': 500, 'pair_additions': 16, 'pair_removals': 8, 'pairs': 150},
                    'refill_shortlist': 24, 'trials': 100000, 'seconds': 14400,
                    'starts': 'C, D, E from the scale150-refine token-input dictionaries (D0, fitted on all 150). CH, DH from the fallback alphabet with greedy refill on the 120 training problems, so the held-out 30 are never seen.'},
         'arms': {'A': 'S1, D0 fixed', 'A0': 'S0, D0 fixed', 'B': 'S2, D0 fixed', 'C': 'S1, search', 'D': 'S2, search', 'E': 'SE, search',
                  'CH': 'S1, search on train 120, fixed dictionary on held-out 30', 'DH': 'S2, search on train 120, fixed dictionary on held-out 30'},
         'metrics': 'Per arm and width, on all 150: total selections, median, p95, worst, single-character selection fraction, source bytes per selection, dictionary and package bytes, problems choosing a style source, per-problem counts. Held-out arms also report train 120 and held-out 30. Every packet is decoded independently through the canonical codec to a qualified source hash.',
         'predictions': {
             'P1': 'At 256 entries, D uses at least 10% fewer selections than C.',
             'P2': 'At 256 entries, D\'s single-character selection fraction is at least 10 points below C\'s.',
             'P3': 'At 256 entries, E uses no more selections than C (style alone beats the whole existing pool).',
             'P4': 'At 128 entries, D uses fewer selections than C.',
             'P5': 'On the held-out 30 at 256 entries, DH uses at least 10% fewer selections than CH.',
             'P6': 'At least 120 of 150 rewrites qualify.'},
         'not_claimed': 'M1 is not measured here (150 is not the frozen 500). No autonomous assembly, unseen solving or BITS promotion follows; a BITS candidate would need BITS_PROMOTION.md on its own cohort slot.',
         'code_hashes': {rel: sha((LIT / rel).read_bytes()) for rel in code}}
    out.write_text(json.dumps(c, indent=1, sort_keys=True) + '\n'); print(sha(out.read_bytes()), len(c['designed_forms']), heldout)


if __name__ == '__main__':
    main()
