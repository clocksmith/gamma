"""Write contract.json for minify-control-v1 (refuses to overwrite)."""
import hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sys.path.insert(0, str(HERE))
sha = lambda b: hashlib.sha256(b).hexdigest()
W = Path('/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1')
SEED = 'minify-control-v1-devval'


def main():
    import minify
    out = HERE / 'contract.json'; assert not out.exists()
    pop = json.loads((LIT / 'admission500-v1/evidence/population-500.json').read_text())
    ids = sorted(r['id'] for r in pop['rows']); assert len(ids) == 500
    cohorts = {k: sorted(r['id'] for r in pop['rows'] if r['cohort'] == k) for k in ('first-150', 'admitted-213', 'gap-137')}
    s500 = json.loads((LIT / 'scale500-v1/contract.json').read_text())
    train = sorted(s500['split']['train']); assert len(train) == 400
    order = sorted(train, key=lambda i: sha(f'{SEED}{i}'.encode()))
    receipt = json.loads((W / 'minify/receipt.json').read_text())
    passed = {r['id'] for r in receipt['rows'] if r['passed']}
    first = set(cohorts['first-150'])
    files = {'O': lambda p: W / 'population500' / f'{p}.js',
             'Om': lambda p: (W / 'minify/om' / f'{p}.js') if p in passed else (W / 'population500' / f'{p}.js'),
             'R': lambda p: W / ('style150' if p in first else 'scale500') / 'submitted' / f'{p}.js'}
    prior = {str(s): str(W / f'style150/run-v2/D-{s}/dictionary.json') for s in (128, 256)}
    code = ['minify-control-v1/control.py', 'minify-control-v1/minify.py', 'minify-control-v1/make_contract.py',
            'minify-control-v1/test_control.py', 'minify-control-v1/FREEZE.md', 'style150-v2/measure.py', 'style150-v1/measure.py',
            'style150-v1/style.py', 'matched80-v3/run.py', 'matched80-v1/run.py', 'joint-v1/search.py', 'joint-v1/audit.py',
            'scale-v2/search.py', 'admission500-v1/stage.py', 'admission500-v1/qualify_rules.py', 'admission500-v1/harness.cjs',
            'admission500-v1/harness-exact-integer.cjs', 'admission500-v1/population.py']
    c = {'schema': 'gamma.minify-control-v1.contract.v1',
         'goal': 'Compaction-only control: original vs terser-minified vs shared-style sources on the frozen 500, fixed and refitted dictionaries',
         'population_sha256': sha((LIT / 'admission500-v1/evidence/population-500.json').read_bytes()),
         'ids': ids, 'cohorts': cohorts,
         'partition': {'seed': SEED, 'rule': 'scale500-v1 training 400, sha256(seed + id) ascending; first 100 dev-val, rest dev-fit',
                       'dev_val': sorted(order[:100]), 'dev_fit': sorted(order[100:]),
                       'final_heldout': 'scale500-v1 held-out 100: no separate measurement; only inside all-500 aggregates'},
         'inputs': {'om_receipt_sha256': sha((W / 'minify/receipt.json').read_bytes()),
                    'om_generation_sha256': sha((W / 'minify/generation.json').read_bytes()),
                    'om_qualified': len(passed), 'terser_sha256': minify.terser_sha(), 'terser_version': '5.46.1',
                    'source_sha256': {k: {str(p): sha(f(p).read_bytes()) for p in ids} for k, f in files.items()},
                    'prior_dictionaries': prior, 'prior_dictionary_sha256': {k: sha(Path(v).read_bytes()) for k, v in prior.items()},
                    'scale500_contract_sha256': sha((LIT / 'scale500-v1/contract.json').read_bytes())},
         'search': {'proposer': 'style150-v2 hybrid_chosen with no designed forms (chosen-source spans only), every arm',
                    'start': 'fallback alphabet (96), greedy refill, matched80-v3 exact local search',
                    'neighborhood': s500['search']['neighborhood'], 'refill_shortlist': 24, 'trials': 60000, 'seconds': 21600,
                    'pythonhashseed': 0},
         'arms': {'search': '3 pools (O, Om, R) x widths 7/8 x fits F500 (all 500) and Fdev (dev-fit 300, measured on dev-val 100)',
                  'fixed': 'A (alphabet), P (style150-v2 D), and each refitted dictionary of the same fit and width, applied to every pool'},
         'm1_gates': '400 of 500 frozen problems; at most 256 entries; median at most 32 and p95 at most 96 selections; at most 10% of selection bits from single-character entries; zero whole-solution entries; compare 128/7 and 256/8. Unchanged.',
         'predictions': {
             'K1': "Om totals at most 75% of O's source bytes, and refitted L-Om at 256 (F500) uses at least 25% fewer selections than refitted L-O.",
             'K2': 'Refitted R at 256 (F500) uses at least 20% fewer selections than refitted Om.',
             'K3': 'Under refitted dictionaries at 256 (F500), R has more bytes per selection than Om.',
             'K4': 'On Om at 256, D_R costs at least 10% more selections than D_Om.',
             'K5': 'On dev-val 100 (Fdev), the order O > Om > R in selections holds at both widths.',
             'K6': 'At least 490 of 500 Om sources qualify.',
             'K7': 'No arm meets M1.',
             'K8': 'Every packet decodes; zero failures.'},
         'not_claimed': 'No M1 qualification, unseen solving, assembly result or BITS profile.',
         'code_hashes': {rel: sha((LIT / rel).read_bytes()) for rel in code}}
    out.write_text(json.dumps(c, indent=1, sort_keys=True) + '\n'); print(sha(out.read_bytes()))


if __name__ == '__main__':
    main()
