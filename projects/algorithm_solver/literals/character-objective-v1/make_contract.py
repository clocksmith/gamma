import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((LIT/'binding-descent-v1/contract.json').read_text());work=Path('/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1')
c={'schema':'gamma.character-objective.v1','partition':old['partition'],'code_hashes':dict(old['code_hashes']),
   'decoder_dependency_bytes':old['decoder_dependency_bytes'],'runtime_files':old['runtime_files'],
   'search':{'trials':12000,'seconds':600},'neighborhood':old['neighborhood'],
   'limits':{'workers':4,'address_space_bytes':4294967296,'overall_seconds':1800},
   'pre_freeze_audit':{'corpus_measurements':False,'tests':6,'exhaustive_examples':100,'weights_per_example':4},
   'seed_path':'binding-descent/run-v1/scope_joint-256','private_files':{}}
for file in ('dictionary.json','fit-sources.json','sources.json','fit-seal.json'):
    rel=c['seed_path']+'/'+file;c['private_files'][rel]=sha(work/rel)
for f in HERE.iterdir():
    if f.suffix=='.py' or f.name=='FREEZE.md':c['code_hashes'][str(f.relative_to(LIT))]=sha(f)
for rel in ('segmentation-audit-v1/segment.py','binding-descent-v1/evidence/results.json','cost-decomposition-v1/evidence/results.json'):
    c['code_hashes'][rel]=sha(LIT/rel)
c['historical_evidence_sha256']=c['code_hashes']['binding-descent-v1/evidence/results.json']
files={str((LIT/rel).resolve()):h for rel,h in c['code_hashes'].items() if rel.endswith(('.py','.cjs')) and '/test_' not in rel};files.update(c['runtime_files'])
c['offline_encoder_files']=files;c['offline_encoder_bytes']=sum(Path(p).stat().st_size for p in files)
c['offline_encoder_scope']='Conservative pinned source dependency closure and parser runtime files; not complete installed runtime.'
(HERE/'contract.json').write_text(json.dumps(c,indent=2,sort_keys=True)+'\n')
