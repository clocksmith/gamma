"""Prelaunch opaque hash pinning only: no source JSON parsing or corpus search."""
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import numpy
import scipy
if not __debug__ or sys.flags.optimize or 'PYTHONOPTIMIZE' in os.environ:
    raise RuntimeError('Optimized Python/PYTHONOPTIMIZE forbidden')
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def spec(p):
    assert p.is_file(),p
    return {'file':str(p.resolve()),'sha256':sha(p)}
old=json.loads((LIT/'python-binding-continuation-v1/contract.json').read_text())
root=Path('/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1/python-binding-continuation/run-v1')
c={'schema':'gamma.python-character-slots.v1','parent_recorded_commit':'84a4c7310','partition':old['partition'],
   'entries':{str(x['id']):x['entry'] for x in old['sources']},'python_bin':sys.executable,
   'versions':{'python':platform.python_version(),'numpy':numpy.__version__,'scipy':scipy.__version__},
   'qualification':spec(LIT/'python-binding-continuation-v1/evidence/results.json'),
   'cores':[4,5,6,7],'overall_seconds':1200,'limits':{'address_space_bytes':8*1024**3},
   'predictions':{'P1':'R validation action totals reproduce1420 at128 and949 at256.',
                  'P2':'At least one optional arm strictly improves fit selections over same-width fixed96.',
                  'P3':'Neither width passes the complete optional-successor gates.',
                  'P4':'All288 output/problem pairs qualify and decode, with no illegal entries.'},
   'search':{'moves':8,'solver_seconds':60,'seconds':600,'checkpoint_reserve_seconds':10,'max_length':64,
             'seed':24,'free_total':{'7':32,'8':48},'free_characters':8,'priority_characters':4,'top':3000,'random':1000},
   'inputs':{},'code_hashes':{},'decoder_source_files':{},'runtime_files':{},'prelaunch_source_contents_parsed':False}
for w in (7,8):
    folder=root/f'w{w}'
    c['inputs'][str(w)]={key:spec(folder/rel) for key,rel in [('fit','scope_joint/fit-sources.json'),('sources','scope_joint/sources.json'),
        ('seed_dictionary','scope_joint/dictionary.json'),('original_sources','control/sources.json'),('baseline_dictionary','baseline-dictionary.json')]}
for rel in ('literals.py','pass2/working/bitpack.py'):
    path=LIT/rel;assert path.is_file();c['decoder_source_files'][rel]={'sha256':sha(path),'bytes':path.stat().st_size}
c['decoder_source_bytes']=sum(x['bytes'] for x in c['decoder_source_files'].values());assert c['decoder_source_bytes']>0
# Exact directly/transitively imported local runtime sources, plus inherited inventory.
for rel in set(old['code_hashes'])|{'character-slots-v1/repair.py','cost-decomposition-v1/analyze.py','tail-search-v1/search.py'}:
    if rel.endswith(('.py','.cjs')):c['code_hashes'][rel]=sha(LIT/rel)
for p in HERE.iterdir():
    if p.suffix=='.py' or p.name in ('DESIGN.md','FREEZE.md'):c['code_hashes'][str(p.relative_to(LIT))]=sha(p)
for p in (Path(sys.executable).resolve(),Path(numpy.__file__),Path(scipy.__file__)):
    c['runtime_files'][str(p)]=sha(p)
# Pin installed binary components used by NumPy/SciPy (including HiGHS).
for package in (numpy,scipy):
    for p in Path(package.__file__).parent.rglob('*.so'):c['runtime_files'][str(p)]=sha(p)
c['offline_encoder_bytes']=sum((LIT/rel).stat().st_size for rel in c['code_hashes'] if rel.endswith(('.py','.cjs')) and '/test_' not in rel)
c['offline_encoder_scope']='Conservative local source inventory; installed runtime/solver footprint unmeasured.'
(HERE/'contract.json').write_text(json.dumps(c,sort_keys=True,indent=2)+'\n')
print(json.dumps({'contract_sha256':sha(HERE/'contract.json'),'source_contents_parsed':False,'fit_count':len(c['partition']['dev_fit']),'validation_count':len(c['partition']['dev_val'])}))
