"""Public-metadata-only D10 binding. Never opens any private source/case file."""
import os
if not __debug__ or os.environ.get("PYTHONOPTIMIZE", "") not in ("", "0"):
    raise RuntimeError("Normal Python assertions required for activation; -O/PYTHONOPTIMIZE forbidden")
import argparse
import copy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())


def build():
    prior=read(LIT/'stacking-v1/contract.json')
    carrier=read(LIT/'stacking-structured-v1/contract.json')
    evidence=read(LIT/'stacking-v1/evidence/results.json')
    assert carrier['source_bound'] and prior['partition']==carrier['partition']
    assert carrier['parent_evidence']['private_results_sha256']==evidence['private_results_sha256']
    assert evidence['predictions']['S1_references_and_all_packets_replay'] is True
    d10=next(a for a in evidence['arms'] if a['arm']=='D10' and a['policy']=='shortest_min_char')
    d11=next(a for a in evidence['arms'] if a['arm']=='D11' and a['policy']=='shortest_min_char')
    expected={str(i) for ids in prior['partition'].values() for i in ids}
    assert set(d10['per_problem'])==set(d11['per_problem'])==expected
    for pid in expected:
        assert d10['per_problem'][pid]['source_sha256']==d11['per_problem'][pid]['source_sha256']==carrier['source_qualification'][pid]['source_sha256']
        assert d10['qualification'][pid]['passed'] and d11['qualification'][pid]['passed']
    assert d10['character_entries']==92 and d10['entries']==256 and not d10['illegal_entry_sha256']
    known={}
    for arm in evidence['arms']:
        for pid,row in arm['per_problem'].items():
            q=arm['qualification'][pid]
            if q['passed']:
                known.setdefault(f'{pid}:{row["source_sha256"]}',{'passed':True,'receipt':q,'source_arm':arm['arm'],'source_policy':arm['policy'],'reused':True})
    source_run=carrier['source_run']
    c={'schema':'gamma.atomic-naming-entry.v1','active':False,'execution_status':'requires_pushed_freeze_and_cross_review',
       'source_arm':'D10','source_run':source_run,'work':str(Path(source_run).parents[1]),
       'source_carrier':{'arm':'D11','provenance':'All400 public D10/D11 per-ID source hashes equal; source bytes only, never D11 dictionary selection.',
                         'private_files':carrier['private_files'],'parent_contract_sha256':sha(LIT/'stacking-structured-v1/contract.json')},
       'initial_dictionary':{'path':'artifacts/D10/dictionary.json','sha256':d10['dictionary_sha256'],
                             'binary_sha256':d10['dictionary_binary_sha256'],'entries':256,'character_entries':92},
       'partition':prior['partition'],'source_qualification':carrier['source_qualification'],'known_receipts':known,
       'parent_evidence':{'path':'stacking-v1/evidence/results.json','sha256':sha(LIT/'stacking-v1/evidence/results.json'),
                          'private_results_sha256':evidence['private_results_sha256'],'contract_sha256':sha(LIT/'stacking-v1/contract.json')},
       'qualification':prior['qualification'],'manifest_sha256':prior['manifest_sha256'],
       'python_bin':prior['python_bin'],'python_version':prior['versions']['python'],
       'all_cores':[0,1,2,3],'cores':[[0],[1],[2],[3]],'limits':{'address_space_bytes':8589934592,'overall_seconds':3600,'worker_seconds':900,'report_seconds':900},
       'search':{'trials':10000,'seconds':600},'policy':'shortest_min_char','validation_passes':2,
       'context_cap':16,'neutral_names':['aa','ab','ac','ad','ae','af','ag','ah'],'prior_palette_cap':4,
       'code_hashes':dict(prior['code_hashes']),'runtime_files':dict(prior['runtime_files']),
       'decoder_dependencies':[str(LIT/'literals.py'),str(LIT/'pass2/working/bitpack.py')],
       'model_bytes':0,'training_steps':0}
    for rel in ('stacking-v1/contract.json','stacking-v1/evidence/results.json','stacking-structured-v1/contract.json',
                'palette-names-v1/palette.py','palette-names-v1/FREEZE.md','palette-names-v1/README.md'):
        c['code_hashes'][rel]=sha(LIT/rel)
    for p in sorted(HERE.iterdir()):
        if p.suffix in ('.py','.md','.cjs'):c['code_hashes'][str(p.relative_to(LIT))]=sha(p)
    c['decoder_dependency_bytes']=sum(Path(p).stat().st_size for p in c['decoder_dependencies'])
    assert c['decoder_dependency_bytes']==13010
    c['offline_encoder_files']={str(LIT/rel):digest for rel,digest in c['code_hashes'].items() if rel.endswith(('.py','.cjs')) and '/test_' not in rel}
    c['offline_encoder_bytes']=sum(Path(p).stat().st_size for p in c['offline_encoder_files'])
    c['runtime_inventory_scope']='Conservative inherited public source/runtime pin inventory; installed runtime footprint unmeasured.'
    return c


def activate(current,pending):
    assert current==pending and pending['active'] is False,'reviewed pending contract drift'
    result=copy.deepcopy(pending);result['active']=True;return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--activate',action='store_true');args=parser.parse_args()
    current=build();pending=HERE/'pending-contract.json'
    if args.activate:
        value=activate(current,read(pending));path=HERE/'contract.json'
    else:value=current;path=pending
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'path':str(path),'sha256':sha(path),'active':value['active'],'private_inputs_opened':False}))


if __name__=='__main__':main()
