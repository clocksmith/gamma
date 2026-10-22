"""Write contract.json for scale500-v1 (refuses to overwrite)."""
import hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sha = lambda b: hashlib.sha256(b).hexdigest()
W = Path('/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1')
SEED = 'scale500-v1-heldout'
TRIALS = {'wide': int(sys.argv[1]), 'heldout': int(sys.argv[2]), 'ils': int(sys.argv[3])}


def main():
    out = HERE / 'contract.json'; assert not out.exists()
    pop = json.loads((LIT / 'admission500-v1/evidence/population-500.json').read_text())
    ids = sorted(r['id'] for r in pop['rows']); assert len(ids) == 500
    order = sorted(ids, key=lambda i: sha(f'{SEED}{i}'.encode()))
    v1 = json.loads((LIT / 'style150-v1/contract.json').read_text())
    starts = {str(s): str(W / f'style150/run-v2/D-{s}/dictionary.json') for s in (128, 256)}
    code = ['scale500-v1/measure.py', 'scale500-v1/rewrite.py', 'scale500-v1/make_contract.py', 'style150-v2/measure.py',
            'style150-v1/measure.py', 'style150-v1/style.py', 'style150-v1/STYLE.md', 'matched80-v3/run.py', 'matched80-v1/run.py',
            'joint-v1/search.py', 'scale-v2/search.py', 'admission500-v1/stage.py', 'admission500-v1/qualify_rules.py',
            'admission500-v1/harness.cjs', 'admission500-v1/harness-exact-integer.cjs', 'admission500-v1/population.py']
    c = {'schema': 'gamma.scale500-v1.contract.v1',
         'goal': 'M1 measurement and vocabulary search at scale on the frozen 500 (literal compression policy, primitive entries only)',
         'population_sha256': sha((LIT / 'admission500-v1/evidence/population-500.json').read_bytes()),
         'cohorts': {k: sorted(r['id'] for r in pop['rows'] if r['cohort'] == k) for k in ('first-150', 'admitted-213', 'gap-137')},
         'split': {'seed': SEED, 'rule': 'sha256(seed + id) ascending; first 100 held out', 'heldout': sorted(order[:100]), 'train': sorted(order[100:])},
         'inputs': {'start_dictionaries': starts, 'start_dictionary_sha256': {k: sha(Path(v).read_bytes()) for k, v in starts.items()},
                    'style150_v1_contract_sha256': sha((LIT / 'style150-v1/contract.json').read_bytes())},
         'rewrites': {'scope': 'the 350 problems outside the first 150, one rewrite each by rewriter agents following style150-v1 STYLE.md',
                      'inputs': 'admitted source and statement; no dictionary, encoding or measurement output',
                      'checks_per_problem': 8, 'qualification': 'all corpus cases of the frozen 500: unchanged oracle plus strict parity with the admitted source (result, type, arguments after, alias edges), with each problem\'s frozen transport and adapter',
                      'failure': 'recorded, not replaced; the problem keeps only its admitted source'},
         'designed_forms': v1['designed_forms'],
         'search': {'proposer': 'style150-v2 hybrid_chosen (3/4 chosen-source spans, 1/4 designed forms)', 'neighborhood': v1['search']['neighborhood'],
                    'refill_shortlist': 24, 'trials': TRIALS, 'seconds': 21600},
         'ils': {'seeds': [1, 2, 3, 4, 5], 'kick': {'128': 4, '256': 8}, 'start': 'W2 of the same size'},
         'arms': {'W1': 'P1, local search from style150-v2 D', 'W2': 'P2, local search from style150-v2 D',
                  'I2-sN': 'P2, seeded iterated local search from W2', 'H1': 'P1, fitted on train 400 from the fallback alphabet, measured on held-out 100',
                  'H2': 'P2, as H1'},
         'm1_gates': '400 of 500 frozen problems; at most 256 entries; median at most 32 and p95 at most 96 selections; at most 10% of selection bits from single-character entries; zero whole-solution entries; compare 128/7 and 256/8. Unchanged.',
         'predictions': {
             'S1': 'At 256 entries, W2 uses at least 25% fewer selections than W1 on all 500.',
             'S2': 'On the held-out 100 at 256 entries, H2 uses at least 15% fewer selections than H1.',
             'S3': 'At least 4 of 5 ILS seeds at 256 entries improve on W2; their spread is at most 1% of the median.',
             'S4': 'M1 is not met by any arm (median above 32 on all 500).',
             'S5': 'At least 300 of the 350 rewrites qualify.'},
         'not_claimed': 'No autonomous assembly or unseen solving; held-out problems are exposed corpus material held out of dictionary fitting only. BITS promotion only under BITS_PROMOTION.md.',
         'code_hashes': {rel: sha((LIT / rel).read_bytes()) for rel in code}}
    out.write_text(json.dumps(c, indent=1, sort_keys=True) + '\n'); print(sha(out.read_bytes()))


if __name__ == '__main__':
    main()
