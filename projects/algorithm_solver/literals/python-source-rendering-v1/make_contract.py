"""Build from public manifests only. --activate is an explicit post-review step."""
import argparse
import copy
import json
import platform
import sys
from pathlib import Path
from common import HERE,LIT,sha,write,require_assertions

def spec(path):return {'file':str(path.resolve()),'sha256':sha(path.read_bytes())}

def build(activate=False):
    require_assertions()
    parent=json.loads((LIT/'python-binding-continuation-v1/contract.json').read_text())
    pins=json.loads((LIT/'python-character-slots-v1/contract.json').read_text())
    assert parent['partition']==pins['partition']
    c={'schema':'gamma.python-source-rendering.v1','execution_authorized':activate,
       'parent_recorded_commit':'84a4c7310','parent_contract':spec(LIT/'python-binding-continuation-v1/contract.json'),
       'anchor_pin_contract':spec(LIT/'python-character-slots-v1/contract.json'),
       'qualification':spec(LIT/'python-binding-continuation-v1/evidence/results.json'),
       'partition':parent['partition'],'sources':parent['sources'],'entries':pins['entries'],'inputs':pins['inputs'],
       'python_bin':str(Path(sys.executable).resolve()),'python_version':platform.python_version(),
       'cores':list(range(8)),'qualification_cores':list(range(4)),
       'overall_seconds':2400,'limits':{'address_space_bytes':8*1024**3,'fit_seconds':300,'validation_seconds':180,
       'qualification_seconds':1800,'report_seconds':600,'qualification_cpu_seconds':3,'qualification_wall_seconds':8,
       'qualification_memory_bytes':512*1024**2,'qualification_output_bytes':4*1024**2,'qualification_batch_cases':32},
       'rounds':2,'search':{'trials':12000,'seconds':60},
       'neighborhood':{'additions':96,'swaps':500,'pairs':150,'pair_additions':16,'pair_removals':8,'designed_fraction':.25},
       'code_hashes':{},'runtime_files':copy.deepcopy(parent['runtime_files']),
       'decoder_source_files':parent['decoder_source_files'],'decoder_source_bytes':parent['decoder_source_bytes'],
       'prelaunch_private_content_read':False,
       'predictions':{'P1':'All 288 experimental views and 72 R reference views decode and qualify, with zero illegal entries.',
        'P2':'At least one width has S validation actions strictly below unchanged U.',
        'P3':'At least one width has J validation actions strictly below searched D.',
        'P4':'At least one width has J validation actions strictly below source-only S.',
        'P5':'No rendering arm passes all strong readiness and incremental gates.'}}
    # Inherit frozen local dependencies; add exactly this implementation and its docs.
    for rel in parent['code_hashes']:
        c['code_hashes'][rel]=sha((LIT/rel).read_bytes())
    for rel in ('python-binding-continuation-v1/backend.py','python-binding-continuation-v1/qualification.py'):
        c['code_hashes'][rel]=sha((LIT/rel).read_bytes())
    for path in HERE.iterdir():
        if path.suffix=='.py' or path.name in ('DRAFT.md','FREEZE.md'):
            c['code_hashes'][str(path.relative_to(LIT))]=sha(path.read_bytes())
    c['offline_encoder_bytes']=sum((LIT/rel).stat().st_size for rel in c['code_hashes'] if rel.endswith(('.py','.cjs')) and '/test_' not in rel)
    c['offline_encoder_scope']='Conservative pinned local source inventory; installed runtime and standard-library footprint unmeasured.'
    return c

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--activate',action='store_true',help='Only after root/Claude prelaunch approval; writes executable contract')
    args=ap.parse_args();c=build(args.activate)
    target=HERE/('contract.json' if args.activate else 'pending-contract.json')
    if args.activate:assert not target.exists(),'no contract overwrite'
    write(target,c)
    print(json.dumps({'file':target.name,'sha256':sha(target.read_bytes()),'execution_authorized':args.activate,'private_content_read':False}))
if __name__=='__main__':main()
