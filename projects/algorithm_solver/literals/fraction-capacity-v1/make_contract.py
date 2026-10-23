"""Pin identities without analyzing corpus contents."""
import hashlib
import json
from pathlib import Path
import platform
import numpy
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((LIT/'character-slots-v1/contract.json').read_text())
c={k:old[k] for k in ('decoder_dependency_bytes','runtime_files','code_hashes')}
c.update(schema='gamma.fraction-capacity.contract.v1',python_bin='/home/x/deco/gamma/.venv_rocm/bin/python',
    versions={'python':platform.python_version(),'numpy':numpy.__version__},fit_ids=old['partition']['dev_fit'],
    cohorts={'R':'binding-descent/run-v1/control-256','naming':'binding-descent/run-v1/scope_joint-256'},
    private_files={},max_length=64,search={'iterations':2000,'seconds':1200,'halve_after':30,'primal_every':25,'denominator':1000000},
    limits={'workers':4,'cores':[8,9,10,11],'address_space_bytes':8589934592,'overall_seconds':2400},
    pre_freeze_audit={'corpus_probe':False,'tests':5,'exhaustive_dictionary_instances':60,'exhaustive_path_instances':60})
work=Path('/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1')
for seedrel in c['cohorts'].values():
    for file in ('dictionary.json','fit-sources.json'):
        rel=seedrel+'/'+file;c['private_files'][rel]=sha(work/rel)
for file in ('dual.py','run.py','test_dual.py','make_contract.py','FREEZE.md'):
    c['code_hashes'][str((HERE/file).relative_to(LIT))]=sha(HERE/file)
c['offline_encoder_files']={str((LIT/rel).resolve()):h for rel,h in c['code_hashes'].items() if rel.endswith(('.py','.cjs')) and '/test_' not in rel}
c['offline_encoder_files'].update({p:h for p,h in c['runtime_files'].items() if p.endswith(('.js','.cjs'))})
c['offline_encoder_bytes']=sum(Path(p).stat().st_size for p in c['offline_encoder_files'])
c['offline_encoder_scope']='Conservative inherited source/parser inventory; full installed interpreter/NumPy runtime footprint is unmeasured.'
(HERE/'contract.json').write_text(json.dumps(c,sort_keys=True,indent=2)+'\n')
