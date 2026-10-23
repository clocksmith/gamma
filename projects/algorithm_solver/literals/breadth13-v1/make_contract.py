"""Writes contract.json for breadth13-v1 (run once, before the freeze commit)."""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sha = lambda p: hashlib.sha256((LIT / p).read_bytes()).hexdigest()
CODE = ['breadth13-v1/succ.py', 'breadth13-v1/evidence.py', 'breadth13-v1/make_contract.py', 'breadth13-v1/FREEZE.md',
        'breadth-lns-v1/breadth.py', 'lagrange-select-v2/selection.py', 'cost-decomposition-v1/analyze.py',
        'cost-decomposition-v1/lexical.cjs', 'literals.py', 'pass2/working/bitpack.py', 'tail-search-v1/structure.cjs']
c = {'schema': 'gamma.breadth13-v1.contract.v1',
     'code_hashes': {p: sha(p) for p in CODE},
     'parent_contract_sha256': sha('cost-decomposition-v1/contract.json'),
     'seed': {'relative_path': 'binding-descent/run-v1/scope_joint-256',
              'private_sha256': {'dictionary.json': 'e3cb3e3cb4017596ca8b8103a39ec5747198a00e143c739ef28393f4215d0c38',
                                 'sources.json': 'ff9a0b3d6f59c770127bba34042e4add527c98055061dd25638fb7b2fbfdc586'}},
     'current_best': {'evidence': 'character-slots-v1/evidence/results.json', 'arm': 'optional',
                      'evidence_sha256': sha('character-slots-v1/evidence/results.json'), 'commit': 'a8b0ff852'},
     'qualification_receipt': 'binding-descent-v1/evidence/results.json',
     'qualification_receipt_sha256': sha('binding-descent-v1/evidence/results.json'),
     'lns': {'k': 40, 'top': 3000, 'random': 1000, 'milp_seconds': 300, 'lns_seconds': 5400, 'seed': 8},
     'relative_scale': 1000000, 'objective_tolerance': 0.25, 'pool_max_length': 64,
     'cores': {'unweighted': [11], 'nonregress': [12], 'relative': [13]},
     'python': '/home/x/deco/gamma/.venv_rocm/bin/python (scipy 1.18.1, HiGHS)'}
(HERE / 'contract.json').write_text(json.dumps(c, indent=1, sort_keys=True) + '\n')
