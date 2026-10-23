"""Create a prospective contract after item11 records; no corpus search or scoring."""
import hashlib
import json
from pathlib import Path
import platform
import sys
import numpy
import scipy
import scipy.optimize._highspy._core as highs
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert (HERE/'FREEZE.md').exists(),'Final freeze waits for item11 record'
old=json.loads((LIT/'coupled-names-v1/contract.json').read_text())
keep=('partition','qualification','manifest_sha256','decoder_dependency_bytes','runtime_files','seed','code_hashes','neighborhood')
c={k:old[k] for k in keep}
c.update(schema='gamma.lns-naming.contract.v1',rounds=2,validation_naming_calls=2,
    python_bin='/home/x/deco/gamma/.venv_rocm/bin/python',
    versions={'python':platform.python_version(),'numpy':numpy.__version__,'scipy':scipy.__version__},
    rewrite={'sweeps':2,'trials':6000},search={'trials':30000,'seconds':600},
    repair={'moves':6,'seconds':900,'solver_seconds':120,'max_length':64,'free':40,'top':3000,'random':1000,'seed':1500},
    search_cores=[[0,1,2,3],[4,5,6,7]],validation_cores=list(range(8)),
    limits={'search_workers':2,'validation_workers':4,'sandbox_workers':4,'address_space_bytes':8589934592,'overall_seconds':7200},
    pre_freeze_audit={'corpus_search_or_cost_probe':False,'synthetic_tests':8})
c['runtime_files'][str(Path(sys.executable).resolve())]=sha(Path(sys.executable).resolve())
c['runtime_files'][highs.__file__]=sha(Path(highs.__file__))
for file in ('engine.py','run.py','test_engine.py','make_contract.py','FREEZE.md'):
    p=HERE/file;c['code_hashes'][str(p.relative_to(LIT))]=sha(p)
for rel in ('lagrange-select-v2/selection.py','mip-lns-v1/lns.py','binding-descent-v1/evidence/results.json'):
    c['code_hashes'][rel]=sha(LIT/rel)
work=Path('/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1')
for rel,digest in c['seed']['files'].items():assert sha(work/c['seed']['relative_path']/rel)==digest,rel
c['offline_encoder_files']={str((LIT/rel).resolve()):h for rel,h in c['code_hashes'].items() if rel.endswith(('.py','.cjs')) and '/test_' not in rel}
c['offline_encoder_files'].update({p:h for p,h in c['runtime_files'].items() if p.endswith(('.js','.cjs'))})
c['offline_encoder_bytes']=sum(Path(p).stat().st_size for p in c['offline_encoder_files'])
c['offline_encoder_scope']='Conservative inherited source/tooling and parser inventory; Python/SciPy/HiGHS binaries pinned separately, complete runtime installation size unmeasured.'
(HERE/'contract.json').write_text(json.dumps(c,sort_keys=True,indent=2)+'\n')
