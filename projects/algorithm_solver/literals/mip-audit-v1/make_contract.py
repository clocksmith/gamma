"""Write contract.json for mip-audit-v1 (refuses to overwrite)."""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sha = lambda b: hashlib.sha256(b).hexdigest()


def main():
    out = HERE / 'contract.json'; assert not out.exists()
    mc = json.loads((LIT / 'minify-control-v1/contract.json').read_text())
    code = ['mip-audit-v1/FREEZE.md', 'mip-audit-v1/audit.py', 'mip-audit-v1/make_contract.py', 'lagrange-select-v2/selection.py',
            'cost-decomposition-v1/analyze.py', 'cost-decomposition-v1/lexical.cjs', 'tail-search-v1/structure.cjs',
            'literals.py', 'pass2/working/bitpack.py', 'style150-v2/measure.py', *mc['code_hashes']]
    c = {'schema': 'gamma.mip-audit-v1.contract.v1', 'B': 32, 'max_length': 32, 'milp_seconds': 900,
         'sizes': [20, 30, 40], 'seeds': {'20': [101, 102, 103, 104, 105, 106], '30': [201, 202, 203, 204, 205, 206],
                                         '40': [301, 302, 303, 304, 305, 306]},
         'excluded_probe_seeds': [1, 2, 3, 4], 'python': '/home/x/deco/gamma/.venv_rocm/bin/python (scipy 1.18.1, HiGHS)',
         'code_hashes': {rel: sha((LIT / rel).read_bytes()) for rel in dict.fromkeys(code)}}
    out.write_text(json.dumps(c, indent=1, sort_keys=True) + '\n'); print(sha(out.read_bytes()))


if __name__ == '__main__':
    main()
