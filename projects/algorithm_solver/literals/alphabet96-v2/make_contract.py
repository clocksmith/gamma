"""Writes contract.json for alphabet96-v2 (run once, before the freeze commit)."""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sha = lambda p: hashlib.sha256((LIT / p).read_bytes()).hexdigest()
HIGHS = '/home/x/deco/gamma/.venv_rocm/lib/python3.14/site-packages/scipy/optimize/_highspy/_core.cpython-314-x86_64-linux-gnu.so'
CODE = ['alphabet96-v2/run.py', 'alphabet96-v2/capped.py', 'alphabet96-v2/evidence.py', 'alphabet96-v2/make_contract.py',
        'alphabet96-v2/FREEZE.md', 'alphabet96-v2/AMENDMENT-1.md', 'alphabet96-v2/test_capped.py', 'lexfrac-v1/evidence/results.json', 'holdout-gate-v1/evidence/results.json', 'alphabet96-v1/evidence/results.json', 'binding-descent-v1/evidence/results.json', 'seeded-repair-v1/model.py',
        'lagrange-select-v2/selection.py', 'cost-decomposition-v1/analyze.py', 'cost-decomposition-v1/lexical.cjs', 'literals.py',
        'pass2/working/bitpack.py', 'tail-search-v1/structure.cjs']
c = {'schema': 'gamma.alphabet96-v2.contract.v1',
     'code_hashes': {p: sha(p) for p in CODE},
     'parent_contract_sha256': sha('cost-decomposition-v1/contract.json'),
     'seed': {'relative_path': 'binding-descent/run-v1/scope_joint-256',
              'dictionary': 'alphabet96/run-v1/drop/dictionary.json',
              'dictionary_sha256': '6a4972f6b46fe1230c5aed839609e970e6e7d0f750608e1a374c7dda9aa5d92a',
              'universe_order_dictionary': 'nonregress24/run-v1/nonregress/dictionary.json',
              'universe_order_dictionary_sha256': 'f53db5b5944fc0834fbca169a36dfde9577bd320feb8f59d45e77f3c6961a702',
              'private_sha256': {'fit-sources.json': '4785b837f53a4798a9005e49d33d9d8e1795d7c83a597d2bc1b133680fbe7063',
                                 'sources.json': 'ff9a0b3d6f59c770127bba34042e4add527c98055061dd25638fb7b2fbfdc586'}},
     'current_best': {'evidence': 'lexfrac-v1/evidence/results.json', 'arm': 'flat',
                      'evidence_sha256': sha('lexfrac-v1/evidence/results.json'), 'commit': '5389ce575'},
     'char_scale': 32768, 'missing_characters': ['B', 'P', 'R', '_'],
     'item51_dictionary': 'lexfrac/run-v1/flat/dictionary.json', 'item51_dictionary_sha256': '75ff15afa292eac704a3376ff268194fe15968bedf026433054e510f3bf2c63d',
     'start_evidence': 'alphabet96-v1/evidence/results.json', 'start_evidence_sha256': sha('alphabet96-v1/evidence/results.json'),
     'item13_dictionary': 'binding-descent/run-v1/scope_joint-256/dictionary.json', 'item13_dictionary_sha256': 'e3cb3e3cb4017596ca8b8103a39ec5747198a00e143c739ef28393f4215d0c38',
     'qualification_receipt': 'binding-descent-v1/evidence/results.json',
     'qualification_receipt_sha256': sha('binding-descent-v1/evidence/results.json'),
     'arms': {'lastdrop': {'k': None, 'repair': False, 'universe': 'last'}, 'repair43': {'k': 24, 'repair': True, 'universe': 'after43'},
              'repairlast': {'k': 24, 'repair': True, 'universe': 'last'}},
     'lns': {'top': 3000, 'random': 1000, 'milp_seconds': 300, 'lns_seconds': 3000, 'seed': 13},
     'objective_tolerance': 0.25, 'pool_max_length': 64,
     'cores': {'lastdrop': [8], 'repair43': [9], 'repairlast': [10]},
     'limits': {'arm_seconds': 4800, 'address_space_bytes': 10 * 2 ** 30},
     'runtime': {'launcher': '/home/x/deco/gamma/.venv_rocm/bin/python', 'python_realpath': '/usr/bin/python3.14',
                 'python_sha256': hashlib.sha256(Path('/usr/bin/python3.14').read_bytes()).hexdigest(), 'python_version': '3.14.4', 'scipy': '1.18.1',
                 'highs_extension_path': HIGHS, 'highs_extension_sha256': hashlib.sha256(Path(HIGHS).read_bytes()).hexdigest()}}
(HERE / 'contract.json').write_text(json.dumps(c, indent=1, sort_keys=True) + '\n')
