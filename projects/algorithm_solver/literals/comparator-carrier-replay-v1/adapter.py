"""Item58 isolated item54 adapter copy with explicit raw/rewritten/binary seed identity.

Public acceptance is a prerequisite, not a substitute for re-encoding each
policy. Only the selected stage's dictionary/results and the pinned item13
source carrier may be read privately. No search or qualification is executed.
"""
import hashlib
import json
import math
from pathlib import Path
import re

STAGES={'48':('tailcap-v1','tailcap',('tail','flat')),
        '51':('lexfrac-v1','lexfrac',('lexnc','flat'))}
SOURCE='binding-descent/run-v1/scope_joint-256'
QUAL='binding-descent-v1/evidence/results.json'
SEED='nonregress24/run-v1/nonregress/dictionary.json'
POLICIES=('canonical','shortest_min_char')


def digest(raw):return hashlib.sha256(raw).hexdigest()


def exact(actual,expected):
    """JSON structural equality with booleans distinct from numeric counters."""
    if isinstance(expected,dict):
        assert isinstance(actual,dict) and set(actual)==set(expected)
        for k,v in expected.items():exact(actual[k],v)
    elif isinstance(expected,list):
        assert isinstance(actual,list) and len(actual)==len(expected)
        for a,b in zip(actual,expected):exact(a,b)
    elif type(expected) in (int,float):
        assert type(actual) is type(expected) and math.isfinite(actual) and actual==expected
    else:assert type(actual) is type(expected) and actual==expected


def pairs(items):
    out={}
    for k,v in items:
        assert k not in out
        out[k]=v
    return out


def summary(aggregate):
    return {'selections':{k:v for k,v in aggregate['selections'].items() if k!='n'},
      'actions':aggregate['actions']['total'],
      **{k:aggregate['actions'][k] for k in ('median','p90','p95')},
      'single_character_fraction':aggregate['single_character_fraction'],
      'package_bytes':aggregate['package_bytes']}


def truth_checks(value):
    assert isinstance(value,dict) and value and all(v is True for v in value.values())


def external(binding,config,index,r,reader):
    assert __debug__
    assert set(binding)=={'recorded_commit','recorded_label','evidence','comparison','parent_contract','dictionary','private_results'}
    assert isinstance(binding['recorded_commit'],str) and re.fullmatch('[0-9a-f]{7,40}',binding['recorded_commit'])
    assert isinstance(binding['recorded_label'],str) and binding['recorded_label']
    comparison=binding['comparison'];assert set(comparison)=={'kind','stage','arm'} and comparison['kind']=='external'
    assert comparison=={'kind':'external','stage':'51','arm':'flat'}
    component,private,arms=STAGES[comparison['stage']];arm=comparison['arm'];assert arm in arms
    allowed={'evidence':component+'/evidence/results.json','parent_contract':component+'/contract.json',
             'dictionary':private+'/run-v1/'+arm+'/dictionary.json','private_results':private+'/run-v1/results.json'}
    for key,path in allowed.items():
        assert set(binding[key])=={'path','sha256'} and binding[key]['path']==path
    assert config['active'] is True and config['source_bound'] is True
    parent=reader(r.c.LIT,allowed['parent_contract'],binding['parent_contract']['sha256'])
    evidence=reader(r.c.LIT,allowed['evidence'],binding['evidence']['sha256'])
    assert evidence['schema']=='gamma.'+component+'.evidence.v1'
    assert evidence['contract_sha256']==binding['parent_contract']['sha256']
    assert evidence['results_sha256']==binding['private_results']['sha256']
    best=evidence['record_time_best'];assert best['resolved'] is True and best['replacement_allowed'] is True
    assert best['selected']==arm and arm in best['eligible']
    accepted=best['per_candidate'][arm];assert accepted['resolved'] is True and accepted['passes'] is True
    truth_checks(accepted['checks'])
    assert arm not in evidence['failed_arms'] and arm in evidence['replayed_arms']
    exact(evidence['exit_codes'][arm],0)
    public=evidence['arms'][arm];assert public['successor'] is True
    truth_checks(public['ready_vs_R']);truth_checks(public['incremental_vs_seed'])
    assert evidence['all_sources_qualified_by_receipt'] is True
    assert parent['qualification_receipt']==evidence['qualification_reused']==QUAL
    q=reader(r.c.LIT,QUAL,parent['qualification_receipt_sha256'])
    matches=[a for a in q['arms'] if a['arm']=='scope_joint' and type(a['width']) is int and a['width']==8]
    assert len(matches)==1;q=matches[0]
    original=reader(r.c.LIT,'cost-decomposition-v1/contract.json',parent['parent_contract_sha256'])
    exact(original['partition'],config['partition'])
    fit=list(map(str,config['partition']['dev_fit']));val=list(map(str,config['partition']['dev_val']))
    ids=set(fit+val);assert len(fit)==300 and len(val)==100 and len(ids)==400
    seed=parent['seed'];assert seed['relative_path']==SOURCE and seed['dictionary']==SEED
    for label,name in (('fit','fit-sources.json'),('all','sources.json')):
        exact(config['sources'][label],{'path':SOURCE+'/'+name,'sha256':seed['private_sha256'][name]})
    assert config['dictionaries']['43N']['path']==SEED
    assert seed['dictionary_sha256']==config['dictionaries']['43N']['sha256']
    prior=index[('43N-U','canonical')]
    assert config['dictionaries']['43N']['sha256']==seed['dictionary_sha256']
    assert set(prior['per_problem'])==ids
    # All public acceptance/path/lineage checks precede any private read.
    original_seed=reader(config['work'],SEED,seed['dictionary_sha256'])
    seed_identity=check_seed(original_seed,index,r,seed['dictionary_sha256'])
    texts=reader(config['work'],SOURCE+'/sources.json',config['sources']['all']['sha256'])
    vocab=reader(config['work'],allowed['dictionary'],binding['dictionary']['sha256'])
    retained=reader(config['work'],allowed['private_results'],binding['private_results']['sha256'])
    assert retained['contract_sha256']==binding['parent_contract']['sha256'];exact(retained['exit_codes'][arm],0)
    selected=[a for a in retained['arms'] if a['arm']==arm];assert len(selected)==1;raw=selected[0]
    assert public['dictionary_sha256']==raw['dictionary_sha256']==binding['dictionary']['sha256']
    assert isinstance(vocab,list) and 1<=len(vocab)==len(set(vocab))<=256
    assert all(isinstance(w,str) and w for w in vocab)
    assert set(texts)==set(q['per_problem'])==set(q['qualification'])==set(raw['per_problem'])==ids
    receipts={}
    for pid,text in texts.items():
        assert isinstance(text,str);h=digest(text.encode())
        assert h==q['per_problem'][pid]['source_sha256']==config['source_qualification'][pid]['source_sha256']==prior['per_problem'][pid]['source_sha256']
        assert q['qualification'][pid]['passed'] is True and config['source_qualification'][pid]['passed'] is True
        assert prior['per_problem'][pid]['qualified_source'] is True and prior['per_problem'][pid]['encodable'] is True
        receipts[pid]={'passed':True,'reused':True,'receipt':QUAL,'source_sha256':h}
    # The owning reporter provides its active old-parser replay and deadline.
    # There is deliberately no implicit parser subprocess fallback here.
    illegal=sorted(digest(w.encode()) for w in set(vocab)&r.external_original_bans(texts))
    exact(illegal,[]);exact(raw['illegal_entry_sha256'],illegal);exact(public['illegal_entry_sha256'],illegal)
    exact(raw['decoded'],400);exact(public['decoded'],400);exact(public['coverage'],{'fit':300,'validation':100})
    binary=r.c.analyze.dictionary_bytes(vocab);db=len(binary);exact(raw['dictionary_bytes'],db)
    decoder=config['decoder_dependency_bytes'];assert type(decoder) is int and decoder>=0
    assert all(type(v) is int and v>=0 for v in evidence['decoder_dependency_bytes'].values())
    assert sum(evidence['decoder_dependency_bytes'].values())==decoder
    policies={}
    for policy in POLICIES:
        rows={}
        for pid,text in sorted(texts.items()):
            codes=r.encode(text,vocab,policy);packet=r.c.analyze.encode(vocab,codes,8)
            assert r.c.analyze.decode(binary,packet)==text
            row={'encodable':True,'selections':len(codes),'actions':len(codes)+1,
                 'single_characters':sum(len(vocab[i])==1 for i in codes),'packet_bytes':len(packet)}
            if policy=='canonical':exact(raw['per_problem'][pid],row)
            row.update(source_sha256=digest(text.encode()),source_bytes=len(text.encode()),source_byte_delta=0,
                       packet_sha256=digest(packet),qualified_source=True,one_program_package_bytes=db+len(packet),
                       one_program_package_with_decoder_dependencies=db+len(packet)+decoder)
            rows[pid]=row
        value={'arm':'external'+comparison['stage']+'/'+arm,'policy':policy,'width':8,'entries':len(vocab),
               'character_entries':sum(len(w)==1 for w in vocab),'dictionary_bytes':db,
               'dictionary_sha256':binding['dictionary']['sha256'],'dictionary_binary_sha256':digest(binary),
               'illegal_entry_sha256':illegal,'per_problem':rows,'qualification':receipts}
        for split,pids in (('fit',fit),('validation',val)):value[split]=r.aggregate(rows,pids,db,decoder)
        policies[policy]=value
    canonical=policies['canonical'];rows=canonical['per_problem'];old=prior['per_problem']
    for split in ('fit','validation'):exact(public[split],summary(canonical[split]))
    exact(public['per_problem_validation_actions'],{pid:rows[pid]['actions'] for pid in val})
    ns={pid:old[pid]['selections'] for pid in fit};nc={pid:rows[pid]['selections'] for pid in fit}
    assert all(type(n) is int and n>0 for n in ns.values())
    recon={'start_fit':sum(ns.values()),'final_fit':sum(nc.values()),
           'fit_programs_worse_than_start':sum(nc[p]>ns[p] for p in fit),
           'fit_programs_better_than_start':sum(nc[p]<ns[p] for p in fit)}
    assert recon['fit_programs_worse_than_start']==0
    if comparison['stage']=='48':
        quantile=parent['tail_quantile'];weight=parent['tail_weight']
        assert type(quantile) in (int,float) and 0<quantile<=1 and type(weight) is int and weight>1
        cutoff=sorted(ns.values())[math.ceil(quantile*len(ns))-1]
        weights={pid:weight if arm=='tail' and ns[pid]>=cutoff else 1 for pid in fit}
        recon.update(tail_programs=sum(w>1 for w in weights.values()),final_objective=sum(weights[p]*nc[p] for p in fit))
    else:
        scale=parent['char_scale'];assert type(scale) is int and scale>0
        assert all(type(old[p]['single_characters']) is int and 0<=old[p]['single_characters']<=ns[p] for p in fit)
        start=sum(old[p]['single_characters'] for p in fit);end=sum(rows[p]['single_characters'] for p in fit)
        recon.update(start_characters=start,final_characters=end,final_objective=scale*sum(nc.values())+end if arm=='lexnc' else sum(nc.values()))
    for key,value in recon.items():exact(public[key],value);exact(raw[key],value)
    return policies,{'resolved':True,'historical_only':True,'seed_carrier_identity':seed_identity,**binding,'binding_sha256':digest(json.dumps(binding,sort_keys=True,separators=(',',':')).encode()),
      'source_carrier_sha256':config['sources']['all']['sha256'],'qualification_receipt_sha256':parent['qualification_receipt_sha256'],
      'sources':400,'decoded_policy_packets':800,'fit_caps_checked':300,'fresh_qualification_jobs':0,
      'comparison_scope':'Accepted external arm; actual ordered dictionary re-encoded independently under canonical and min-N/min-C policies. Canonical totals reconciled with public evidence and hash-bound private results.'}



def check_seed(vocab,index,r,raw_hash):
    assert isinstance(vocab,list) and 1<=len(vocab)==len(set(vocab))<=256
    assert all(type(w) is str and w for w in vocab)
    rewritten=(json.dumps(vocab,sort_keys=True,indent=2)+'\n').encode()
    binary=r.c.analyze.dictionary_bytes(vocab)
    for view in ('43N-U','43N-S'):
        for policy in POLICIES:
            old=index[view,policy]
            exact(old['dictionary_sha256'],digest(rewritten))
            exact(old['dictionary_binary_sha256'],digest(binary))
            exact(old['dictionary_bytes'],len(binary))
            exact(old['entries'],len(vocab))
            exact(old['character_entries'],sum(len(w)==1 for w in vocab))
    return {'original_json_sha256':raw_hash,'item54_rewritten_json_sha256':digest(rewritten),
      'ordered_binary_sha256':digest(binary),'dictionary_bytes':len(binary),
      'entries':len(vocab),'character_entries':sum(len(w)==1 for w in vocab)}
