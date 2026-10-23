"""Freeze current code/seed/runtime identities without a corpus cost probe."""
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((LIT/'coupled-names-v1/contract.json').read_text())
c={k:old[k] for k in ('partition','qualification','manifest_sha256','decoder_dependency_bytes','runtime_files','seed','code_hashes','neighborhood','search')}
c.update(schema='gamma.syntax-choice.contract.v1',rewrite={'moves':20,'trials':2000,'proposals':256},
    limits={'search_workers':2,'sandbox_workers':4,'cores':[8,9,10,11],'address_space_bytes':4294967296,'overall_seconds':3600},
    pre_freeze_audit={'corpus_probe_or_extraction':False,'python_tests':4,'synthetic_behavior_observations':127})
for file in ('alternatives.cjs','rewrite.py','run.py','test_alternatives.cjs','test_rewrite.py','make_contract.py','FREEZE.md'):
    p=HERE/file;c['code_hashes'][str(p.relative_to(LIT))]=sha(p)
c['code_hashes']['binding-descent-v1/evidence/results.json']=sha(LIT/'binding-descent-v1/evidence/results.json')
c['offline_encoder_files']={str((LIT/rel).resolve()):h for rel,h in c['code_hashes'].items() if rel.endswith(('.py','.cjs')) and '/test_' not in rel}
c['offline_encoder_files'].update({p:h for p,h in c['runtime_files'].items() if p.endswith(('.js','.cjs'))})
c['offline_encoder_bytes']=sum(Path(p).stat().st_size for p in c['offline_encoder_files'])
c['offline_encoder_scope']='Conservative inherited source/tooling and parser inventory, not complete runtime installation storage.'
(HERE/'contract.json').write_text(json.dumps(c,sort_keys=True,indent=2)+'\n')
