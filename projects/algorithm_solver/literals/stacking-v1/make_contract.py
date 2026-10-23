"""Pin existing artifacts and code; no corpus analysis or source transformation."""
import hashlib
import json
from pathlib import Path
import platform
import numpy
import scipy

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
WORK = Path('/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
old = read(LIT/'lns-naming-v1/contract.json')
c = {key: old[key] for key in ('partition', 'decoder_dependency_bytes', 'qualification', 'manifest_sha256', 'neighborhood')}
c.update(schema='gamma.stacking.flat.v1', execution_status='requires_pushed_freeze_and_cross_review',
         python_bin='/home/x/deco/gamma/.venv_rocm/bin/python',
         versions={'python': platform.python_version(), 'numpy': numpy.__version__, 'scipy': scipy.__version__},
         references={'R': 'binding-descent/run-v1/control-256',
                     'seed13': 'binding-descent/run-v1/scope_joint-256',
                     'best24': 'character-slots/run-v1/optional'},
         private_files={}, code_hashes={}, runtime_files={}, source_rounds=2,
         source_search={'seconds': 300, 'trials': 12000},
         weighted_search={'seconds': 300, 'trials': 30000},
         rewrite={'sweeps': 2, 'trials': 6000, 'rounds': 3, 'proposal_limit': 512, 'state_limit': 100000},
         repair={'moves': 4, 'seconds': 600, 'solver_seconds': 120, 'max_length': 64,
                 'free_total': 48, 'free_characters': 8, 'priority_characters': 4,
                 'top': 3000, 'random': 1000, 'seed': 2800},
         all_cores=list(range(8)), source_cores=[[0,1],[2,3],[4,5],[6,7]],
         repair_cores=[[0,1,2,3],[4,5,6,7]],
         limits={'search_workers': 4, 'sandbox_workers': 4, 'address_space_bytes': 8589934592,
                 'overall_seconds': 7200, 'termination_grace_seconds': 30},
         structured_sidecar_executed=False)
for parent in ('lns-naming-v1', 'compiler-choice-v1', 'coupled-names-v1',
               'segmentation-audit-v1', 'character-objective-v1',
               'character-slots-v1', 'seeded-repair-v1'):
    prior = read(LIT/parent/'contract.json')
    for field in ('code_hashes', 'runtime_files'):
        for path, digest in prior.get(field, {}).items():
            if path in c[field]:
                assert c[field][path] == digest, (field, path)
            c[field][path] = digest
for name in ('R', 'seed13'):
    for file in ('dictionary.json', 'fit-sources.json', 'sources.json'):
        rel = c['references'][name]+'/'+file
        c['private_files'][rel] = sha(WORK/rel)
rel = c['references']['best24']+'/dictionary.json'
c['private_files'][rel] = sha(WORK/rel)
for file in ('coverage_search.py', 'engine.py', 'run.py', 'launch.py', 'make_contract.py',
             'test_coverage_search.py', 'test_engine.py', 'test_report.py', 'FREEZE.md', 'AMENDMENT-1.md'):
    c['code_hashes'][str((HERE/file).relative_to(LIT))] = sha(HERE/file)
for rel in ('binding-descent-v1/evidence/results.json', 'lns-naming-v1/evidence/results.json',
            'character-slots-v1/evidence/results.json'):
    c['code_hashes'][rel] = sha(LIT/rel)
c['reference_validation'] = {}
old13 = read(LIT/'binding-descent-v1/evidence/results.json')['arms']
old24 = read(LIT/'character-slots-v1/evidence/results.json')['arms']
for name, row in [('R', next(a for a in old13 if a['arm']=='control' and a['width']==8)),
                  ('seed13', next(a for a in old13 if a['arm']=='scope_joint' and a['width']==8)),
                  ('best24', next(a for a in old24 if a['arm']=='optional'))]:
    d = row['validation']
    c['reference_validation'][name] = {'actions': d['actions']['total'],
                                      'selections': d['selections']['total'],
                                      'single_character_fraction': d['single_character_fraction'],
                                      'package_bytes': d['package_bytes']}
c['offline_encoder_files'] = {str((LIT/path).resolve()): digest for path, digest in c['code_hashes'].items()
                              if path.endswith(('.py','.cjs')) and '/test_' not in path}
c['offline_encoder_files'].update({path:digest for path,digest in c['runtime_files'].items()
                                   if path.endswith(('.js','.cjs'))})
c['offline_encoder_bytes'] = sum(Path(path).stat().st_size for path in c['offline_encoder_files'])
c['offline_encoder_scope'] = 'Conservative source/parser/compiler inventory. Pinned Python/SciPy/solver binaries are not a complete measured runtime installation.'
(HERE/'contract.json').write_text(json.dumps(c, sort_keys=True, indent=2)+'\n')
