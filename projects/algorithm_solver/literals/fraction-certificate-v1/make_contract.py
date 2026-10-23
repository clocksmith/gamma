import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((LIT/'segmentation-audit-v1/contract.json').read_text())
c={k:v for k,v in old.items() if k in ('partition','code_hashes','decoder_dependency_bytes','historical_evidence_sha256')}
c.update(schema='gamma.fraction-certificate.contract.v1',max_iterations=64,seeds=[],private_files={},
         pre_freeze_audit={'corpus_measurement':False,'synthetic_tests':5},limits={'cores':[8],'address_space_bytes':1073741824,'seconds':600})
work=Path('/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1')
for name,arm,width in [('R128','control',7),('R256','control',8),('naming256','scope_joint',8)]:
    rel=f'binding-descent/run-v1/{arm}-{2**width}';c['seeds'].append({'name':name,'arm':arm,'width':width,'relative_path':rel})
    for file in ('dictionary.json','sources.json'):c['private_files'][rel+'/'+file]=sha(work/rel/file)
for file in ('ratio.py','run.py','test_ratio.py','make_contract.py','FREEZE.md'):
    p=HERE/file;c['code_hashes'][str(p.relative_to(LIT))]=sha(p)
c['code_hashes']['segmentation-audit-v1/segment.py']=sha(LIT/'segmentation-audit-v1/segment.py')
c['code_hashes']['binding-descent-v1/evidence/results.json']=sha(LIT/'binding-descent-v1/evidence/results.json')
c['offline_tooling_bytes']=sum((LIT/rel).stat().st_size for rel in c['code_hashes'] if rel.endswith(('.py','.cjs')) and '/test_' not in rel)
(HERE/'contract.json').write_text(json.dumps(c,sort_keys=True,indent=2)+'\n')
