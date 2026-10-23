"""Writes contract.json for warm-nonregress-v1 (run once, before the freeze commit)."""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sha = lambda p: hashlib.sha256((LIT / p).read_bytes()).hexdigest()
CODE = ['warm-nonregress-v1/warm.py', 'warm-nonregress-v1/capped.py', 'warm-nonregress-v1/evidence.py', 'warm-nonregress-v1/make_contract.py',
        'warm-nonregress-v1/FREEZE.md', 'warm-nonregress-v1/test_capped.py', 'seeded-repair-v1/model.py', 'character-slots-v1/repair.py',
        'breadth-lns-v1/breadth.py', 'lagrange-select-v2/selection.py', 'cost-decomposition-v1/analyze.py',
        'cost-decomposition-v1/lexical.cjs', 'literals.py', 'pass2/working/bitpack.py', 'tail-search-v1/structure.cjs']
c = {'schema': 'gamma.warm-nonregress-v1.contract.v1',
     'code_hashes': {p: sha(p) for p in CODE},
     'parent_contract_sha256': sha('cost-decomposition-v1/contract.json'),
     'seed': {'relative_path': 'binding-descent/run-v1/scope_joint-256',
              'private_sha256': {'dictionary.json': 'e3cb3e3cb4017596ca8b8103a39ec5747198a00e143c739ef28393f4215d0c38',
                                 'fit-sources.json': '4785b837f53a4798a9005e49d33d9d8e1795d7c83a597d2bc1b133680fbe7063',
                                 'sources.json': 'ff9a0b3d6f59c770127bba34042e4add527c98055061dd25638fb7b2fbfdc586'}},
     'current_best': {'evidence': 'character-slots-v1/evidence/results.json', 'arm': 'optional',
                      'evidence_sha256': sha('character-slots-v1/evidence/results.json'), 'commit': 'a8b0ff852'},
     'qualification_receipt': 'binding-descent-v1/evidence/results.json',
     'qualification_receipt_sha256': sha('binding-descent-v1/evidence/results.json'),
     'lns': {'k': 40, 'top': 3000, 'random': 1000, 'milp_seconds': 300, 'lns_seconds': 3600, 'seed': 8},
     'objective_tolerance': 0.25, 'pool_max_length': 64,
     'cores': {'warm': [8], 'cold': [9]},
     'limits': {'arm_seconds': 5400, 'address_space_bytes': 10 * 2 ** 30},
     'runtime': {'launcher': '/home/x/deco/gamma/.venv_rocm/bin/python', 'python_realpath': '/usr/bin/python3.14',
                 'python_sha256': hashlib.sha256(Path('/usr/bin/python3.14').read_bytes()).hexdigest(), 'python_version': '3.14.4', 'scipy': '1.18.1'}}
(HERE / 'contract.json').write_text(json.dumps(c, indent=1, sort_keys=True) + '\n')
