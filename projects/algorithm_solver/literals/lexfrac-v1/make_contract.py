"""Writes contract.json for lexfrac-v1 (run once, before the freeze commit)."""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sha = lambda p: hashlib.sha256((LIT / p).read_bytes()).hexdigest()
HIGHS = '/home/x/deco/gamma/.venv_rocm/lib/python3.14/site-packages/scipy/optimize/_highspy/_core.cpython-314-x86_64-linux-gnu.so'
CODE = ['lexfrac-v1/run.py', 'lexfrac-v1/capped.py', 'lexfrac-v1/evidence.py', 'lexfrac-v1/make_contract.py',
        'lexfrac-v1/FREEZE.md', 'lexfrac-v1/AMENDMENT-1.md', 'lexfrac-v1/test_capped.py', 'nonregress24-v1/evidence/results.json', 'seeded-repair-v1/model.py', 'character-slots-v1/repair.py',
        'breadth-lns-v1/breadth.py', 'lagrange-select-v2/selection.py', 'cost-decomposition-v1/analyze.py',
        'cost-decomposition-v1/lexical.cjs', 'literals.py', 'pass2/working/bitpack.py', 'tail-search-v1/structure.cjs']
c = {'schema': 'gamma.lexfrac-v1.contract.v1',
     'code_hashes': {p: sha(p) for p in CODE},
     'parent_contract_sha256': sha('cost-decomposition-v1/contract.json'),
     'seed': {'relative_path': 'binding-descent/run-v1/scope_joint-256',
              'dictionary': 'nonregress24/run-v1/nonregress/dictionary.json',
              'dictionary_sha256': 'f53db5b5944fc0834fbca169a36dfde9577bd320feb8f59d45e77f3c6961a702',
              'private_sha256': {'fit-sources.json': '4785b837f53a4798a9005e49d33d9d8e1795d7c83a597d2bc1b133680fbe7063',
                                 'sources.json': 'ff9a0b3d6f59c770127bba34042e4add527c98055061dd25638fb7b2fbfdc586'}},
     'current_best': {'evidence': 'nonregress24-v1/evidence/results.json', 'arm': 'nonregress',
                      'evidence_sha256': sha('nonregress24-v1/evidence/results.json'), 'commit': 'ded5c3fef'},
     'char_scale': 32768,
     'qualification_receipt': 'binding-descent-v1/evidence/results.json',
     'qualification_receipt_sha256': sha('binding-descent-v1/evidence/results.json'),
     'lns': {'k': 40, 'top': 3000, 'random': 1000, 'milp_seconds': 300, 'lns_seconds': 3000, 'seed': 8},
     'objective_tolerance': 0.25, 'pool_max_length': 64,
     'cores': {'lexnc': [8], 'flat': [9]},
     'limits': {'arm_seconds': 4800, 'address_space_bytes': 10 * 2 ** 30},
     'runtime': {'launcher': '/home/x/deco/gamma/.venv_rocm/bin/python', 'python_realpath': '/usr/bin/python3.14',
                 'python_sha256': hashlib.sha256(Path('/usr/bin/python3.14').read_bytes()).hexdigest(), 'python_version': '3.14.4', 'scipy': '1.18.1',
                 'highs_extension_path': HIGHS, 'highs_extension_sha256': hashlib.sha256(Path(HIGHS).read_bytes()).hexdigest()}}
(HERE / 'contract.json').write_text(json.dumps(c, indent=1, sort_keys=True) + '\n')
