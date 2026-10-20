"""Stage only the permitted phase's retained sources for a clean reproduction."""
import argparse,hashlib,json,shutil
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--run',type=Path,required=True);p.add_argument('--phase',choices=['fit','heldback'],required=True);a=p.parse_args();c=json.loads((a.archive/'contract.json').read_text())
if a.phase=='fit':
 a.run.mkdir(exist_ok=False)
 for name in ['contract.json','generate.cjs','checks.py','verify.py','search.py','evaluate-heldback.py','test-generate.cjs','test-search.py']:shutil.copy2(a.archive/name,a.run/name)
else:
 f=json.loads((a.run/'vocabulary-freeze.json').read_text());assert sha((a.run/'contract.json').read_bytes())==f['contract_sha256']
 for name,digest in f['implementation_sha256'].items():assert sha((a.run/name).read_bytes())==digest
archive_phase='fit-generated-v1' if a.phase=='fit' else 'heldback-generated'
ids=sorted(i for cluster in c['clusters'].values() for i in cluster[a.phase])
for i in ids:
 row=c['selected'][str(i)];source=a.archive/archive_phase/'sources'/f'{i:04d}-original.js';raw=source.read_bytes();assert sha(raw)==row['sha256'];target=a.run/'inputs'/row['relative_path'];target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb') as out:out.write(raw)
print(json.dumps({'phase':a.phase,'source_count':len(ids),'contract_sha256':sha((a.run/'contract.json').read_bytes())}))
