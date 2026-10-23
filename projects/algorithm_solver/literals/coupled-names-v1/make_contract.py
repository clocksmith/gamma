"""Freeze code/runtime/seed hashes without executing a corpus search."""
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((LIT/'binding-descent-v1/contract.json').read_text())
c.pop('fit_only_preflight',None)
c['schema']='gamma.coupled-names.v1';c['stage']='coupled-names-v1'
c['pre_freeze_audit']={'corpus_cost_measurements':False,'synthetic_tests':9}
c['rewrite']={'sweeps':2,'trials':6000,'rounds':3,'proposal_limit':512,'state_limit':100000}
for f in HERE.iterdir():
    if f.suffix in ('.py','.cjs') or f.name=='FREEZE.md':c['code_hashes'][str(f.relative_to(LIT))]=sha(f)
work=Path('/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1')
seed=work/'binding-descent/run-v1'
files=[f'{name}/{file}' for name in ('control-256','scope_joint-256') for file in ('dictionary.json','fit-sources.json','fit-variants.json','fit-seal.json','sources.json','results.json')]
c['seed']={'relative_path':'binding-descent/run-v1','files':{rel:sha(seed/rel) for rel in files}}
encoder={str((LIT/rel).resolve()):digest for rel,digest in c['code_hashes'].items() if rel.endswith(('.py','.cjs')) and '/test_' not in rel}
encoder.update(c['runtime_files']);c['offline_encoder_files']=encoder
c['offline_encoder_bytes']=sum(Path(p).stat().st_size for p in encoder)
c['offline_encoder_scope']='Pinned source dependencies and parser/scope runtime files; conservative inherited tooling closure, not complete runtime installation.'
(HERE/'contract.json').write_text(json.dumps(c,indent=2,sort_keys=True)+'\n')
