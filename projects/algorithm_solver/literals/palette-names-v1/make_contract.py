"""Write contract.json for palette-names-v1 (refuses to overwrite)."""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
W = Path('/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1')
sha = lambda b: hashlib.sha256(b).hexdigest()


def main():
    out = HERE / 'contract.json'; assert not out.exists()
    mc = json.loads((LIT / 'minify-control-v1/contract.json').read_text())
    seed = 'binding-descent/run-v1/scope_joint-256'
    receipts = ['binding-descent-v1/evidence/results.json', 'coupled-names-v1/evidence/results.json', 'lns-naming-v1/evidence/results.json']
    code = ['palette-names-v1/FREEZE.md', 'palette-names-v1/palette.py', 'palette-names-v1/evidence.py', 'palette-names-v1/test_palette.py',
            'palette-names-v1/make_contract.py', 'binding-descent-v1/rewrite.py', 'binding-descent-v1/bindings.cjs', 'clusters-v1/search.py',
            'cost-decomposition-v1/analyze.py', 'tail-search-v1/search.py', 'tail-search-v1/structure.cjs', 'style150-v2/measure.py',
            'minify-control-v1/minify.py', *receipts, *mc['code_hashes']]
    c = {'schema': 'gamma.palette-names-v1.contract.v1',
         'seed': {'relative_path': seed, 'private_sha256': {f: sha((W / seed / f).read_bytes()) for f in ('dictionary.json', 'fit-sources.json', 'sources.json')}},
         'palette': {'cap': 40, 'max_length': 12}, 'rewrite': {'sweeps': 2, 'trials': 6000},
         'search': {'trials': 30000, 'seconds': 600}, 'neighborhood': mc['search']['neighborhood'],
         'cores': {'seed': [16], 'az_fixed': [17, 18], 'palette_fixed': [19, 20], 'az_joint': [21, 22], 'palette_joint': [23, 24, 25]},
         'qualified_receipts': receipts,
         'code_hashes': {rel: sha((LIT / rel).read_bytes()) for rel in dict.fromkeys(code)}}
    out.write_text(json.dumps(c, indent=1, sort_keys=True) + '\n'); print(sha(out.read_bytes()))


if __name__ == '__main__':
    main()
