"""Writes contract.json for python-slackcap-v1 (run once, before the freeze commit)."""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sha = lambda p: hashlib.sha256((LIT / p).read_bytes()).hexdigest()
ROOT = '/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1/'
HIGHS = '/home/x/deco/gamma/.venv_rocm/lib/python3.14/site-packages/scipy/optimize/_highspy/_core.cpython-314-x86_64-linux-gnu.so'
CODE = ['python-slackcap-v1/run.py', 'python-slackcap-v1/capped.py', 'python-slackcap-v1/evidence.py', 'python-slackcap-v1/make_contract.py',
        'python-slackcap-v1/FREEZE.md', 'python-slackcap-v1/test_python.py', 'python-ratiocap-v1/evidence/results.json', 'python-ratiocap-v2/evidence/results.json', 'python-related-v1/evidence/results.json', 'python-character-slots-v1/common.py',
        'character-slots-v1/repair.py', 'tail-search-v1/search.py', 'seeded-repair-v1/model.py', 'breadth-lns-v1/breadth.py',
        'lagrange-select-v2/selection.py', 'cost-decomposition-v1/analyze.py', 'literals.py', 'pass2/working/bitpack.py',
        'python-binding-continuation-v1/evidence/results.json', 'python-character-slots-v1/contract.json']
parent = json.loads((LIT / 'python-character-slots-v1/contract.json').read_text())  # item 34: inputs, entries, partition (public)
inputs = {w: {k: {'relative_path': v['file'].split(ROOT, 1)[1], 'sha256': v['sha256']} for k, v in spec.items()} for w, spec in parent['inputs'].items()}
c = {'schema': 'gamma.python-slackcap-v1.contract.v1',
     'code_hashes': {p: sha(p) for p in CODE},
     'inputs': inputs, 'entries': parent['entries'], 'partition': parent['partition'],
     'qualification': {'file': str(LIT / 'python-binding-continuation-v1/evidence/results.json'),
                       'sha256': sha('python-binding-continuation-v1/evidence/results.json')},
     'lns': {'top': 3000, 'random': 1000, 'milp_seconds': 120, 'lns_seconds': 900, 'seed': 10, 'removal_seed': 1010},
     'arms': {'w8s1': {'width': 8, 'seed': 'item69_w8lex', 'k': 48, 'objective': 'lexnc', 'ratio': False, 'removal': 'random', 'slack': 1},
              'w8s3': {'width': 8, 'seed': 'item69_w8lex', 'k': 48, 'objective': 'lexnc', 'ratio': False, 'removal': 'random', 'slack': 3},
              'w7s1': {'width': 7, 'seed': 'item69_w7ratio', 'k': 8, 'objective': 'lexnc', 'ratio': True, 'removal': 'random', 'slack': 1},
              'w7s3': {'width': 7, 'seed': 'item69_w7ratio', 'k': 8, 'objective': 'lexnc', 'ratio': True, 'removal': 'random', 'slack': 3}},
     'seeds': {'item69_w8lex': {'relative_path': 'python-ratiocap/run-v1/w8lex/dictionary.json',
                                'sha256': '9496813aa818a03a2da83195b7410b02a7b468bfa866cd8d34a60fc4dd7619a4'},
               'item69_w7ratio': {'relative_path': 'python-ratiocap/run-v1/w7ratio/dictionary.json',
                                  'sha256': 'c9aa9e66096f7fef7822de6756b16e91b93d88ed0da398364c75f62161dd0fea'}},
     'char_scale': 32768,
     'objective_tolerance': 0.25, 'pool_max_length': 64,
     'gates': {'ready_action_fraction': 0.05, 'improved_min': 6, 'worsened_max': 2},
     'cores': {'w8s1': [0], 'w8s3': [1], 'w7s1': [2], 'w7s3': [4]},
     'limits': {'arm_seconds': 1800, 'address_space_bytes': 8 * 2 ** 30},
     'runtime': {'launcher': '/home/x/deco/gamma/.venv_rocm/bin/python', 'python_realpath': '/usr/bin/python3.14',
                 'python_sha256': hashlib.sha256(Path('/usr/bin/python3.14').read_bytes()).hexdigest(), 'python_version': '3.14.4', 'scipy': '1.18.1',
                 'highs_extension_path': HIGHS, 'highs_extension_sha256': hashlib.sha256(Path(HIGHS).read_bytes()).hexdigest()}}
assert parent['inputs']['7']['seed_dictionary']['sha256'] == parent['inputs']['7']['baseline_dictionary']['sha256']  # w7 anchor is R itself
(HERE / 'contract.json').write_text(json.dumps(c, indent=1, sort_keys=True) + '\n')
