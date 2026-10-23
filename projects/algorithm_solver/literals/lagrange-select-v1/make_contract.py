"""Write contract.json for lagrange-select-v1 (refuses to overwrite)."""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sha = lambda b: hashlib.sha256(b).hexdigest()


def main():
    out = HERE / 'contract.json'; assert not out.exists()
    mc = json.loads((LIT / 'minify-control-v1/contract.json').read_text())
    code = ['lagrange-select-v1/FREEZE.md', 'lagrange-select-v1/selection.py', 'lagrange-select-v1/test_select.py', 'lagrange-select-v1/make_contract.py',
            'cost-decomposition-v1/analyze.py', 'cost-decomposition-v1/lexical.cjs', 'tail-search-v1/structure.cjs',
            'literals.py', 'pass2/working/bitpack.py', 'style150-v2/measure.py', *mc['code_hashes']]
    c = {'schema': 'gamma.lagrange-select-v1.contract.v1',
         'parent_contract_sha256': sha((LIT / 'cost-decomposition-v1/contract.json').read_bytes()),
         'pool': {'min_length': 2, 'max_length': 64, 'min_fit_owners': 2, 'excluded': 'complete sources, solve definitions and bodies'},
         'lagrange': {'iterations': 4000, 'seconds': 3000, 'theta': 1.0, 'halve_after': 30, 'primal_every': 10},
         'polish': {'trials': 60000, 'seconds': 3600, 'refill_shortlist': mc['search']['refill_shortlist'], 'neighborhood': mc['search']['neighborhood']},
         'code_hashes': {rel: sha((LIT / rel).read_bytes()) for rel in dict.fromkeys(code)}}
    out.write_text(json.dumps(c, indent=1, sort_keys=True) + '\n'); print(sha(out.read_bytes()))


if __name__ == '__main__':
    main()
