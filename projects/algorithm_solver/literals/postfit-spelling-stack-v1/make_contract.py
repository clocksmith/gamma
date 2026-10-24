"""Public-only binding after BOTH item43 arms are independently recorded; no probes."""
import argparse
import copy
from pathlib import Path
import common as c


def original_source_authority(c24,c43,optional,q13,partition):
    """Item13/24/43 lineage only; item41 D10 sources are not this population."""
    assert c24['partition']==partition
    assert c43['seed']['relative_path']==c24['seed_relative_path']
    for name in ('fit-sources.json','sources.json'):
        rel=c24['seed_relative_path']+'/'+name
        assert c43['seed']['private_sha256'][name]==c24['private_files'][rel]
    ids={str(i) for group in partition.values() for i in group}
    assert set(optional['per_problem'])==set(q13['per_problem'])==ids
    result={}
    for pid in ids:
        h=q13['per_problem'][pid]['source_sha256']
        assert h==optional['per_problem'][pid]['source_sha256']
        assert q13['qualification'][pid]['passed'] and optional['per_problem'][pid]['qualified_source']
        result[pid]={'source_sha256':h,'passed':True}
    return result


def build():
    evidence43=c.LIT/'nonregress24-v1/evidence/results.json'
    if not evidence43.exists():raise RuntimeError('Both independently recorded item43 arms are required; no binding written')
    old=c.read(c.LIT/'atomic-naming-entry-v1/contract.json');c43=c.read(c.LIT/'nonregress24-v1/contract.json')
    e43=c.read(evidence43);e24=c.read(c.LIT/'character-slots-v1/evidence/results.json')
    c24=c.read(c.LIT/'character-slots-v1/contract.json')
    e41=c.read(c.LIT/'atomic-naming-entry-v1/evidence/results.json')
    parent=c.read(c.LIT/'stacking-v1/evidence/results.json')
    assert e24['contract_sha256']==c.hashfile(c.LIT/'character-slots-v1/contract.json')
    assert e43['contract_sha256']==c.hashfile(c.LIT/'nonregress24-v1/contract.json')
    assert not e43['failed_arms'] and e43['exit_codes']=={'nonregress':0,'unweighted':0}
    assert sorted(e43['replayed_arms'])==['nonregress','unweighted'] and e43['all_sources_qualified_by_receipt'] is True
    assert e41['complete'] is True and e41['independent_replay'] is True
    assert e41['contract_sha256']==c.hashfile(c.LIT/'atomic-naming-entry-v1/contract.json')
    ids={str(i) for group in old['partition'].values() for i in group}
    assert len(old['partition']['dev_fit'])==300 and len(old['partition']['dev_val'])==100 and len(ids)==400
    optional=next(a for a in e24['arms'] if a['arm']=='optional')
    assert optional['dictionary_sha256']==c43['seed']['dictionary_sha256'] and not optional['illegal_entry_sha256']
    assert set(optional['per_problem'])==ids and all(r['encodable'] and r['qualified_source'] for r in optional['per_problem'].values())
    q13path=c.LIT/c43['qualification_receipt'];assert c.hashfile(q13path)==c43['qualification_receipt_sha256']
    q13=next(a for a in c.read(q13path)['arms'] if a['arm']=='scope_joint' and a['width']==8)
    sourceq=original_source_authority(c24,c43,optional,q13,old['partition']);known={}
    for pid in ids:
        h=sourceq[pid]['source_sha256']
        known[f'{pid}:{h}']={'passed':True,'reused':True,'receipt':q13['qualification'][pid],
                            'source_arm':'item24/item43 original scope_joint','source_policy':'canonical'}
    for arm in e41['arms']:
        assert set(arm['per_problem'])==ids
        for pid,row in arm['per_problem'].items():
            q=arm['qualification'][pid]
            if q['passed']:
                known.setdefault(f'{pid}:{row["source_sha256"]}',{'passed':True,'reused':True,'receipt':q,
                    'source_arm':'item41/'+arm['arm'],'source_policy':arm['policy']})
    dictionaries={'24':{'path':c43['seed']['dictionary'],'sha256':optional['dictionary_sha256'],
        'binary_sha256':optional['dictionary_binary_sha256'],'entries':optional['entries'],'character_entries':optional['character_entries']}}
    for anchor,name in [('43N','nonregress'),('43W','unweighted')]:
        arm=e43['arms'][name]
        assert arm['coverage']=={'fit':300,'validation':100} and not arm['illegal_entry_sha256'] and arm['decoded']==400
        dictionaries[anchor]={'path':f'nonregress24/run-v1/{name}/dictionary.json','sha256':arm['dictionary_sha256'],
            'binary_sha256':None,'entries':None,'character_entries':optional['character_entries'],
            'parent_seal':f'nonregress24/run-v1/{name}/fit-seal.json'}
    work=old['work'];assert isinstance(work,str)
    result={k:copy.deepcopy(old[k]) for k in ('partition','qualification','manifest_sha256','python_bin','python_version',
                'code_hashes','runtime_files','decoder_dependencies','decoder_dependency_bytes')}
    result.update(schema='gamma.postfit-spelling-stack.v1',active=False,source_bound=True,work=work,
        source_qualification=sourceq,known_receipts=known,dictionaries=dictionaries,
        sources={label:{'path':c43['seed']['relative_path']+'/'+name,'sha256':c43['seed']['private_sha256'][name]}
                 for label,name in [('fit','fit-sources.json'),('all','sources.json')]},
        deferred_parent_artifacts=[{'path':'nonregress24/run-v1/results.json','sha256':e43['results_sha256']}],
        all_cores=[0,1,2,3],arm_cores={'24':[0],'43N':[1],'43W':[2]},proposal_cap=153600,
        limits={'address_space_bytes':8*1024**3,'overall_seconds':3600,'worker_seconds':1800,
                'qualification_seconds':900,'report_seconds':1800,'cleanup_seconds':10},
        policy='shortest_min_char',passes=2,context_cap=16,neutral_names=['aa','ab','ac','ad','ae','af','ag','ah'],prior_palette_cap=4,
        standing_reference_evidence={'path':'stacking-v1/evidence/results.json','sha256':c.hashfile(c.LIT/'stacking-v1/evidence/results.json'),
                                    'private_results_sha256':parent['private_results_sha256']},
        parent_evidence={},model_bytes=0,training_steps=0,prebinding_private_access=False)
    for anchor,name,arm in [('24','character-slots-v1','optional'),('43N','nonregress24-v1','nonregress'),('43W','nonregress24-v1','unweighted')]:
        result['parent_evidence'][anchor]={'path':name+'/evidence/results.json','sha256':c.hashfile(c.LIT/name/'evidence/results.json'),
            'arm':arm,'contract_path':name+'/contract.json','contract_sha256':c.hashfile(c.LIT/name/'contract.json')}
    # Keep inherited execution pins byte-exact, adding actual public evidence and
    # this implementation. No live parent/private directory is inspected here.
    for name in ('atomic-naming-entry-v1','nonregress24-v1','character-slots-v1','stacking-v1'):
        for tail in ('contract.json','evidence/results.json'):
            path=c.LIT/name/tail;result['code_hashes'][str(path.relative_to(c.LIT))]=c.hashfile(path)
    for path in sorted(c.HERE.iterdir()):
        if path.suffix in ('.py','.md','.cjs'):result['code_hashes'][str(path.relative_to(c.LIT))]=c.hashfile(path)
    result['runtime_files'][str(Path(result['python_bin']).resolve())]=c.hashfile(Path(result['python_bin']).resolve())
    result['offline_encoder_files']={str(c.LIT/rel):h for rel,h in result['code_hashes'].items() if rel.endswith(('.py','.cjs')) and '/test_' not in rel}
    result['offline_encoder_bytes']=sum(Path(p).stat().st_size for p in result['offline_encoder_files'])
    result['runtime_inventory_scope']='Inherited pinned implementations; installed runtime footprint unmeasured.'
    return result


def activate(current,pending):
    assert current==pending and pending['active'] is False and pending['source_bound'] is True,'Reviewed pending drift or unbound parents'
    result=copy.deepcopy(pending);result['active']=True;return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--activate',action='store_true');args=ap.parse_args()
    value=build();path=c.HERE/'pending-contract.json'
    if args.activate:value=activate(value,c.read(path));path=c.HERE/'contract.json'
    c.write(path,value);print(c.canonical({'path':str(path),'sha256':c.hashfile(path),'active':value['active'],'private_inputs_opened':False}))

if __name__=='__main__':main()
