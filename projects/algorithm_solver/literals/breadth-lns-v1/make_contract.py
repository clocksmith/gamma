"""Write contract.json for breadth-lns-v1 (refuses to overwrite)."""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sha = lambda b: hashlib.sha256(b).hexdigest()


def main():
    out = HERE / 'contract.json'; assert not out.exists()
    code = ['breadth-lns-v1/FREEZE.md', 'breadth-lns-v1/breadth.py', 'breadth-lns-v1/test_breadth.py', 'breadth-lns-v1/make_contract.py',
            'lagrange-select-v2/selection.py', 'cost-decomposition-v1/analyze.py', 'cost-decomposition-v1/lexical.cjs',
            'tail-search-v1/structure.cjs', 'literals.py', 'pass2/working/bitpack.py']
    c = {'schema': 'gamma.breadth-lns-v1.contract.v1', 'pool_max_length': 64, 'relative_scale': 1000000,
         'parent_contract_sha256': sha((LIT / 'cost-decomposition-v1/contract.json').read_bytes()),
         'lns': {'k': 40, 'top': 3000, 'random': 1000, 'milp_seconds': 300, 'lns_seconds': 5400, 'seed': 8},
         'cores': {'unweighted': [26, 27], 'nonregress': [28, 29], 'relative': [30, 31]},
         'python': '/home/x/deco/gamma/.venv_rocm/bin/python (scipy 1.18.1, HiGHS)',
         'code_hashes': {rel: sha((LIT / rel).read_bytes()) for rel in dict.fromkeys(code)}}
    out.write_text(json.dumps(c, indent=1, sort_keys=True) + '\n'); print(sha(out.read_bytes()))


if __name__ == '__main__':
    main()
