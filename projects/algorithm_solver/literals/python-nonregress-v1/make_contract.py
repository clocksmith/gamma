"""Writes contract.json for python-nonregress-v1 (run once, before the freeze commit)."""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sha = lambda p: hashlib.sha256((LIT / p).read_bytes()).hexdigest()
ROOT = '/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1/'
HIGHS = '/home/x/deco/gamma/.venv_rocm/lib/python3.14/site-packages/scipy/optimize/_highspy/_core.cpython-314-x86_64-linux-gnu.so'
CODE = ['python-nonregress-v1/run.py', 'python-nonregress-v1/capped.py', 'python-nonregress-v1/evidence.py', 'python-nonregress-v1/make_contract.py',
        'python-nonregress-v1/FREEZE.md', 'python-nonregress-v1/AMENDMENT-1.md', 'python-nonregress-v1/test_python.py', 'python-character-slots-v1/common.py',
        'character-slots-v1/repair.py', 'tail-search-v1/search.py', 'seeded-repair-v1/model.py', 'breadth-lns-v1/breadth.py',
        'lagrange-select-v2/selection.py', 'cost-decomposition-v1/analyze.py', 'literals.py', 'pass2/working/bitpack.py',
        'python-binding-continuation-v1/evidence/results.json', 'python-character-slots-v1/contract.json']
parent = json.loads((LIT / 'python-character-slots-v1/contract.json').read_text())  # item 34: inputs, entries, partition (public)
inputs = {w: {k: {'relative_path': v['file'].split(ROOT, 1)[1], 'sha256': v['sha256']} for k, v in spec.items()} for w, spec in parent['inputs'].items()}
c = {'schema': 'gamma.python-nonregress-v1.contract.v1',
     'code_hashes': {p: sha(p) for p in CODE},
     'inputs': inputs, 'entries': parent['entries'], 'partition': parent['partition'],
     'qualification': {'file': str(LIT / 'python-binding-continuation-v1/evidence/results.json'),
                       'sha256': sha('python-binding-continuation-v1/evidence/results.json')},
     'lns': {'top': 3000, 'random': 1000, 'milp_seconds': 120, 'lns_seconds': 900, 'seed': 8},
     'arm_overrides': {'w7': {'k': 32}, 'w8': {'k': 48}},
     'objective_tolerance': 0.25, 'pool_max_length': 64,
     'gates': {'ready_action_fraction': 0.05, 'improved_min': 6, 'worsened_max': 2},
     'cores': {'w7': [8], 'w8': [9]},
     'limits': {'arm_seconds': 1800, 'address_space_bytes': 8 * 2 ** 30},
     'runtime': {'launcher': '/home/x/deco/gamma/.venv_rocm/bin/python', 'python_realpath': '/usr/bin/python3.14',
                 'python_sha256': hashlib.sha256(Path('/usr/bin/python3.14').read_bytes()).hexdigest(), 'python_version': '3.14.4', 'scipy': '1.18.1',
                 'highs_extension_path': HIGHS, 'highs_extension_sha256': hashlib.sha256(Path(HIGHS).read_bytes()).hexdigest()}}
assert parent['inputs']['7']['seed_dictionary']['sha256'] == parent['inputs']['7']['baseline_dictionary']['sha256']  # w7 anchor is R itself
(HERE / 'contract.json').write_text(json.dumps(c, indent=1, sort_keys=True) + '\n')
