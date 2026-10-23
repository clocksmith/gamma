"""Write contract.json for neartie-audit-v1 (refuses to overwrite)."""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
W = Path('/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1')
sha = lambda b: hashlib.sha256(b).hexdigest()
CC, CN = 'compiler-choice-v1/evidence/results.json', 'coupled-names-v1/evidence/results.json'
ARMS = [('compiler_control128', 'control', 7, 'compiler-choice/run-v1/control-128', CC),
        ('compiler_joint128', 'joint', 7, 'compiler-choice/run-v1/joint-128', CC),
        ('coupled_seed256', 'seed', 8, 'coupled-names/run-v1/seed-256', CN),
        ('coupled_control256', 'control', 8, 'coupled-names/run-v1/control-256', CN),
        ('coupled256', 'coupled', 8, 'coupled-names/run-v1/coupled-256', CN),
        ('coupled_joint256', 'coupled_joint', 8, 'coupled-names/run-v1/coupled_joint-256', CN)]
COMPARISONS = [
    {'label': 'item10 joint128 vs control128', 'candidate': 'compiler_joint128', 'comparator': 'compiler_control128', 'rule': 'ready',
     'expected_historical_failed': ['fraction_not_higher']},
    {'label': 'item14 coupled_joint vs seed', 'candidate': 'coupled_joint256', 'comparator': 'coupled_seed256', 'rule': 'successor',
     'expected_historical_failed': ['fraction_not_higher']},
    {'label': 'item14 coupled vs seed', 'candidate': 'coupled256', 'comparator': 'coupled_seed256', 'rule': 'successor',
     'expected_historical_failed': ['fraction_not_higher']},
    {'label': 'item14 coupled_joint vs control', 'candidate': 'coupled_joint256', 'comparator': 'coupled_control256', 'rule': 'ready',
     'expected_historical_failed': []}]


def main():
    out = HERE / 'contract.json'; assert not out.exists()
    code = ['neartie-audit-v1/FREEZE.md', 'neartie-audit-v1/audit.py', 'neartie-audit-v1/make_contract.py', 'segmentation-audit-v1/segment.py',
            'cost-decomposition-v1/analyze.py', 'literals.py', 'pass2/working/bitpack.py', CC, CN]
    arms = [{'name': n, 'arm': a, 'width': w, 'relative_path': r, 'evidence': e, 'evidence_sha256': sha((LIT / e).read_bytes()),
             'private_sha256': {f: sha((W / r / f).read_bytes()) for f in ('sources.json', 'dictionary.json')}} for n, a, w, r, e in ARMS]
    c = {'schema': 'gamma.neartie-audit-v1.contract.v1', 'arms': arms, 'comparisons': COMPARISONS,
         'code_hashes': {rel: sha((LIT / rel).read_bytes()) for rel in dict.fromkeys(code)}}
    out.write_text(json.dumps(c, indent=1, sort_keys=True) + '\n'); print(sha(out.read_bytes()))


if __name__ == '__main__':
    main()
