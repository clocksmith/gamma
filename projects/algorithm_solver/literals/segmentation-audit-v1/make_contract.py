import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((LIT/'binding-descent-v1/contract.json').read_text());work=Path('/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1')
c={'schema':'gamma.segmentation-audit.v1','partition':old['partition'],'code_hashes':dict(old['code_hashes']),
   'decoder_dependency_bytes':old['decoder_dependency_bytes'],'limits':{'workers':1,'address_space_bytes':1073741824,'overall_seconds':600},
   'pre_freeze_audit':{'corpus_measurements':False,'tests':4,'exhaustive_examples':150,'policies_per_example':4},'seeds':[],'private_files':{}}
for name,arm,w in [('control128','control',7),('control256','control',8),('scope256','scope',8),('scope_joint256','scope_joint',8)]:
    rel=f'binding-descent/run-v1/{arm}-{2**w}';c['seeds'].append({'name':name,'arm':arm,'width':w,'relative_path':rel})
    for file in ('dictionary.json','sources.json','fit-seal.json'):c['private_files'][rel+'/'+file]=sha(work/rel/file)
for f in HERE.iterdir():
    if f.suffix=='.py' or f.name=='FREEZE.md':c['code_hashes'][str(f.relative_to(LIT))]=sha(f)
c['historical_evidence_sha256']=sha(LIT/'binding-descent-v1/evidence/results.json');c['code_hashes']['binding-descent-v1/evidence/results.json']=c['historical_evidence_sha256']
c['offline_extra_encoder_bytes']=sum((HERE/f).stat().st_size for f in ('segment.py','run.py'))
(HERE/'contract.json').write_text(json.dumps(c,indent=2,sort_keys=True)+'\n')
