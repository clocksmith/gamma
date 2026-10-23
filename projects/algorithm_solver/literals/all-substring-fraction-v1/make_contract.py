"""Build metadata-only contract; never opens private corpus inputs."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
parent_path = LIT/'all-length-fraction-v1/contract.json'
parent = json.loads(parent_path.read_text())
c = {key: parent[key] for key in (
    'decoder_dependency_bytes', 'runtime_files', 'code_hashes', 'python_bin',
    'versions', 'fit_ids', 'cohorts', 'private_files', 'offline_encoder_scope')}
c.update(
    schema='gamma.all-substring-fraction.contract.v1',
    parent_contract_sha256=sha(parent_path),
    pool={'scope': 'All nonempty substrings of the exact fixed fit sources, including one-owner words, minus exact complete-source and solve-definition/body bans.',
          'minimum_length': 1, 'maximum_length': None,
          'minimum_distinct_programs': 1, 'mandatory_entries': 0, 'capacity': 256,
          'seed_union_needed': False, 'semantic_reuse_audit': 'not_performed_relaxation_only'},
    search={'iterations': 2000, 'seconds': 1200, 'denominator': 1000000,
            'halve_after': 30, 'primal_every': 25,
            'multiplier_family': 'one nonnegative multiplier per source start',
            'witness_depths': ['shortest_allowed', 'longest_allowed']},
    limits={'workers': 2, 'arm_cores': {'R': [0], 'naming': [1]},
            'address_space_bytes': 8589934592, 'overall_seconds': 2400},
    pre_freeze_audit={'corpus_probe': False, 'tests': 11,
                      'random_explicit_pool_comparisons': 180,
                      'exhaustive_tiny_dictionary_searches': 40})
c['code_hashes']['all-length-fraction-v1/contract.json'] = sha(parent_path)
for name in ('implicit.py', 'optimize.py', 'run.py', 'supervise.py', 'make_contract.py',
             'test_implicit.py', 'test_optimize.py', 'DRAFT.md', 'FREEZE.md'):
    c['code_hashes'][str((HERE/name).relative_to(LIT))] = sha(HERE/name)
c['offline_encoder_files'] = {str((LIT/rel).resolve()): digest for rel, digest in c['code_hashes'].items()
                              if rel.endswith(('.py', '.cjs')) and '/test_' not in rel}
c['offline_encoder_files'].update({path: digest for path, digest in c['runtime_files'].items()
                                   if path.endswith(('.js', '.cjs'))})
c['offline_encoder_bytes'] = sum(Path(path).stat().st_size for path in c['offline_encoder_files'])
(HERE/'contract.json').write_text(json.dumps(c, indent=2, sort_keys=True)+'\n')
