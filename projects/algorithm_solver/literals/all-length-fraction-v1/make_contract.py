"""Inherit previously pinned fit identities without opening corpus files."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
LIT=HERE.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((LIT/'fraction-capacity-v1/contract.json').read_text())
c={k:old[k] for k in ('decoder_dependency_bytes','runtime_files','code_hashes','python_bin','versions','fit_ids','cohorts','private_files','search','offline_encoder_scope')}
c.update(schema='gamma.all-length-fraction.contract.v1',
    parent_contract_sha256=sha(LIT/'fraction-capacity-v1/contract.json'),
    pool={'minimum_length':2,'maximum_length':None,'minimum_distinct_programs':2,
          'bans':'complete fit sources and extracted solve definitions/bodies',
          'seed_learned_union':True,'mandatory_entries':0,'optional_characters':96,'capacity':256},
    limits={'workers':2,'arm_cores':{'R':[0],'naming':[1]},'address_space_bytes':8589934592,'overall_seconds':2400},
    pre_freeze_audit={'corpus_probe':False,'tests':6,'exhaustive_pool_instances':500,'exhaustive_suffix_array_instances':300})
assert c['search']['iterations']==2000 and c['search']['seconds']==1200
for file in ('pool.py','run.py','test_pool.py','make_contract.py','FREEZE.md'):
    c['code_hashes'][str((HERE/file).relative_to(LIT))]=sha(HERE/file)
c['code_hashes']['fraction-capacity-v1/contract.json']=sha(LIT/'fraction-capacity-v1/contract.json')
c['offline_encoder_files']={str((LIT/rel).resolve()):h for rel,h in c['code_hashes'].items() if rel.endswith(('.py','.cjs')) and '/test_' not in rel}
c['offline_encoder_files'].update({p:h for p,h in c['runtime_files'].items() if p.endswith(('.js','.cjs'))})
c['offline_encoder_bytes']=sum(Path(p).stat().st_size for p in c['offline_encoder_files'])
(HERE/'contract.json').write_text(json.dumps(c,sort_keys=True,indent=2)+'\n')
