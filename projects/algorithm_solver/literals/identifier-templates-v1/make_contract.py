import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((LIT/'binding-descent-v1/contract.json').read_text());work=Path('/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1')
c={'schema':'gamma.identifier-templates.v1','partition':old['partition'],'code_hashes':dict(old['code_hashes']),
   'runtime_files':old['runtime_files'],'search':{'trials':12000,'seconds':600},
   'limits':{'workers':4,'address_space_bytes':4294967296,'overall_seconds':1800},
   'pre_freeze_audit':{'corpus_extraction_or_measurement':False,'tests':12},'private_files':{},'cohorts':[],
   'decoder_dependencies':{'literal':[str(LIT/'literals.py'),str(LIT/'pass2/working/bitpack.py')],
                           'typed':[str(HERE/'decoder.cjs'),'/usr/share/nodejs/acorn/dist/acorn.js']}}
for name,arm in [('R','control'),('naming','scope_joint')]:
    rel=f'binding-descent/run-v1/{arm}-256';c['cohorts'].append({'name':name,'arm':arm,'relative_path':rel})
    for file in ('dictionary.json','fit-sources.json','sources.json','fit-seal.json'):c['private_files'][rel+'/'+file]=sha(work/rel/file)
for f in HERE.iterdir():
    if f.suffix in ('.py','.cjs') or f.name=='FREEZE.md':c['code_hashes'][str(f.relative_to(LIT))]=sha(f)
c['historical_evidence_sha256']=sha(LIT/'binding-descent-v1/evidence/results.json');c['code_hashes']['binding-descent-v1/evidence/results.json']=c['historical_evidence_sha256']
c['offline_tooling_bytes']=sum((LIT/rel).stat().st_size for rel in c['code_hashes'] if rel.endswith(('.py','.cjs')) and '/test_' not in rel)+sum(Path(p).stat().st_size for p in c['runtime_files'])
(HERE/'contract.json').write_text(json.dumps(c,indent=2,sort_keys=True)+'\n')
