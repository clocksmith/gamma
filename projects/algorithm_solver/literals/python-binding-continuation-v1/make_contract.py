"""Hash allowed existing artifacts; no source parsing/search/performance probe."""
import copy
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent_path=LIT/'python-name-v1/contract.json';old=json.loads(parent_path.read_text())
c=copy.deepcopy(old)
c.update(schema='gamma.python-binding-continuation.v1',python_bin=str(Path('/usr/bin/python3').resolve()),
         search={'trials':30000,'seconds':600},rewrite={'sweeps':2,'trials':6000},
         search_cores=[2,3],sandbox_cores=[2,3,4,5],
         parent_results_sha256=sha(LIT/'python-name-v1/evidence/results.json'),
         baseline_dictionaries={},pre_freeze_audit={'corpus_probe':False,'synthetic_only':True})
work=Path('/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1/python-name/run-v1')
for w in (7,8):
    p=work/f'w{w}'/'baseline-dictionary.json';c['baseline_dictionaries'][str(w)]={'file':str(p),'sha256':sha(p)}
for name in ('graph.py','backend.py','run.py','qualification.py','launch.py','make_contract.py','test_graph.py','test_pipeline.py','FREEZE.md','AMENDMENT-1.md'):
    p=HERE/name;c['code_hashes'][str(p.relative_to(LIT))]=sha(p)
for rel in ('python-name-v1/contract.json','python-name-v1/evidence/results.json','binding-descent-v1/rewrite.py','lns-naming-v1/engine.py'):
    c['code_hashes'][rel]=sha(LIT/rel)
c['offline_encoder_files']={str((LIT/rel).resolve()):h for rel,h in c['code_hashes'].items() if rel.endswith(('.py','.cjs')) and '/test_' not in rel}
c['offline_encoder_bytes']=sum(Path(p).stat().st_size for p in c['offline_encoder_files'])
c['offline_encoder_scope']='Conservative inherited source inventory; installed interpreter/stdlib/runtime footprint unmeasured.'
c['decoder_source_files']={}
for rel in ('literals.py','pass2/working/bitpack.py'):
    path=LIT/rel
    assert path.is_file(),f'required decoder source missing: {rel}'
    c['decoder_source_files'][rel]={'sha256':sha(path),'bytes':path.stat().st_size}
    c['code_hashes'][rel]=sha(path)
c['decoder_source_bytes']=sum(row['bytes'] for row in c['decoder_source_files'].values())
assert c['decoder_source_bytes']>0
(HERE/'contract.json').write_text(json.dumps(c,sort_keys=True,indent=2)+'\n')
print(json.dumps({'contract_sha256':sha(HERE/'contract.json'),'allowed_source_rows':len(c['sources']),'corpus_loaded':False}))
