"""Supplied-input joint caps; no loader, optimizer or corpus runner.

The complete item57 baseline and a separate item53 potential context are
explicitly reconstructed. Numeric local shared weights and all-arc schedules
are new; frozen dependencies are neither changed nor monkeypatched.
"""
import heapq
import importlib.util
from pathlib import Path

_spec=importlib.util.spec_from_file_location('joint_cap_parent57',Path(__file__).resolve().parents[1]/'owner-path-cap-v1/caps.py')
prior=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(prior)
parent=prior.parent

BASE57_FIELDS=('schema','owner_caps','owner_top_entries','owner_entry_counts','owner_prefixes',
    'capped_prefixes','one_owner_prefix','marginal_choices','shared_prefix','rows','deltas_vs53')
BASE53_FIELDS=('schema','lifted','tightened','new_only_class_counts','new_only_top_entries',
    'digests','reductions','deltas')
COMMON_FIELDS=('local_shared_top_entries','local_shared_prefixes','local_shared_counts','all_caps',
    'split_rows','rows','deltas_vs57')


def scientific57(base):
    return {**{key:base[key] for key in BASE57_FIELDS},
            'base':{key:base['base'][key] for key in BASE53_FIELDS}}


def allocate(owner_prefixes,local_shared_prefixes,all_caps,one,shared,total,D,capacity):
    """Exact concave split allocation, preserving the nonzero shared baseline."""
    splits=[];offers=0;pops=0
    for values in owner_prefixes.values():
        assert values[0]==0
        increments=[b-a for a,b in zip(values,values[1:])]
        assert all(value>=0 for value in increments)
        assert all(a>=b for a,b in zip(increments,increments[1:]))
    for j in range(len(one)):
        s=capacity-j;local={pid:values[min(s,len(values)-1)] for pid,values in local_shared_prefixes.items()}
        baseline=sum(min(local[pid],all_caps[pid]) for pid in owner_prefixes)
        frontier=[]

        def marginal(pid,rank):
            values=owner_prefixes[pid];cap=all_caps[pid];offset=local[pid]
            value=min(offset+values[rank],cap)-min(offset+values[rank-1],cap)
            assert value>=0
            return value

        for pid,values in sorted(owner_prefixes.items()):
            if len(values)>1:
                heapq.heappush(frontier,(-marginal(pid,1),pid,1));offers+=1
        choices=[];joint=baseline
        for _ in range(j):
            assert frontier,'finite real owner entries must cover this split'
            negative,pid,rank=heapq.heappop(frontier);pops+=1
            choices.append((pid,rank,-negative));joint-=negative
            if rank+1<len(owner_prefixes[pid]):
                value=marginal(pid,rank+1);assert value<=-negative
                heapq.heappush(frontier,(-value,pid,rank+1));offers+=1
        available=min(s,len(shared)-1);old=shared[available]+one[j]
        splits.append({'one_owner_slots':j,'shared_slots':s,'shared_slots_available':available,
            'baseline':baseline,'joint_charge':joint,'prior57_charge':old,'charge':min(joint,old),
            'allocation_choices':choices})
    rows=[];best=None
    for k in range(capacity+1):
        if k<len(splits) and (best is None or splits[k]['charge']>best['charge']):best=splits[k]
        assert best is not None
        numerator=total-best['charge']
        rows.append({'k':k,'charge':best['charge'],'one_owner_slots':best['one_owner_slots'],
            'shared_slots':best['shared_slots_available'],'numerator':numerator,
            'integer_lower_bound':-(-numerator//D)})
    return splits,rows,offers,pops


def check(texts,banned,old_pool,old_q,seed,alphabet,D,*,expected_source_hashes,
          expected_old_banned,expected_old_certificate=None,
          expected_occurrence_sha256=None,capacity=256):
    if not __debug__:raise RuntimeError('normal assertions required')
    assert type(capacity) is int and capacity>=0
    kwargs=dict(expected_source_hashes=expected_source_hashes,expected_old_banned=expected_old_banned,
        expected_old_certificate=expected_old_certificate,expected_occurrence_sha256=expected_occurrence_sha256)
    base=prior.check(texts,banned,old_pool,old_q,seed,alphabet,D,capacity=capacity,**kwargs)
    obj=parent.Tighten(texts,banned,old_pool,old_q,seed,alphabet,D,
        old_source_hashes=expected_source_hashes,old_banned=expected_old_banned,
        expected_old_certificate=expected_old_certificate,expected_occurrence_sha256=expected_occurrence_sha256)
    assert obj.path_numerators==base['base']['tightened']['path_numerators']
    assert obj.occurrence_sha256==base['base']['tightened']['occurrence_sha256']
    identities=sorted((gid,length,eid) for (gid,length),eid in obj.old_entry_ids.items() if obj.support[gid]==2)
    assert len(identities)==base['base']['tightened']['class_counts'][2]
    by_eid={eid:(gid,length) for gid,length,eid in identities}
    sums={eid:0 for eid in by_eid};entries={};prefixes={};counts={}
    inspected=0;contributions=0;zero_inspected=0;max_accumulator=0
    for pid,rows in sorted(obj.rows.items()):
        local={};d=obj.d[pid]
        for start,outgoing in enumerate(rows):
            for end,eid,_ in outgoing:
                inspected+=1
                if eid not in by_eid:continue
                value=max(0,d[start]-d[end]-(9 if end-start==1 else -1)*D)
                local[eid]=local.get(eid,0)+value;sums[eid]+=value;contributions+=1
        max_accumulator=max(max_accumulator,len(local))
        top=parent.Top(capacity);positive=set()
        for eid,weight in local.items():
            if weight:
                positive.add(eid);top.add(weight,*by_eid[eid])
        if len(positive)<min(capacity,len(identities)):
            for gid,length,eid in identities:
                if len(top.heap)>=min(capacity,len(identities)):break
                zero_inspected+=1
                if eid not in positive:top.add(0,gid,length)
        entries[pid]=top.entries();prefixes[pid]=prior.prefix(entries[pid])
        counts[pid]={'available':len(identities),'occurring':len(local),'positive':len(positive)}
        assert len(entries[pid])==min(capacity,len(identities))
    assert inspected==obj.old_occurrences
    global_top=parent.Top(capacity)
    for eid,total in sums.items():
        assert total==obj.tight_weights[eid]
        global_top.add(total,*by_eid[eid])
    assert global_top.entries()==base['base']['tightened']['top_entries'][2]
    schedules={};caps={};endpoints=0;admitted=0
    for pid,text in sorted(texts.items()):
        values=[0]*(len(text)+1);d=obj.d[pid]
        for end in range(1,len(text)+1):
            best=values[end-1]
            for start in range(end):
                endpoints+=1
                if end in obj.index.banned_ends[pid][start]:continue
                admitted+=1
                q=max(0,d[start]-d[end]-(9 if end-start==1 else -1)*D)
                best=max(best,values[start]+q)
            values[end]=best
        schedules[pid]=values;caps[pid]=values[-1]
    assert admitted==sum(g['multiplicity']*(g['hi']-g['lo']) for g in obj.index.groups)
    splits,rows,offers,pops=allocate(base['owner_prefixes'],prefixes,caps,
        base['one_owner_prefix'],base['shared_prefix'],sum(obj.path_numerators.values()),D,capacity)
    deltas=[]
    for old,new in zip(base['rows'],rows):
        assert old['k']==new['k'] and new['charge']<=old['charge']
        deltas.append({'k':new['k'],'charge_reduction':old['charge']-new['charge'],
            'integer_bound_gain':new['integer_lower_bound']-old['integer_lower_bound']})
    result={'schema':'gamma.joint-path-cap.supplied.v1','base57':base,
        'local_shared_top_entries':entries,'local_shared_prefixes':prefixes,'local_shared_counts':counts,
        'all_caps':caps,'all_prefix_schedule':schedules,'split_rows':splits,'rows':rows,'deltas_vs57':deltas}
    result['digests']={key+'_sha256':parent.digest(result[key]) for key in COMMON_FIELDS+('all_prefix_schedule',)}
    result['digests']['base57_sha256']=parent.digest(scientific57(base))
    result['work']={'baseline57_reconstructions':1,'additional53_contexts':1,
        'old_occurrences_inspected':inspected,'local_shared_occurrence_contributions':contributions,
        'zero_identity_inspections':zero_inspected,'max_local_accumulator_entries':max_accumulator,
        'retained_local_shared_entries':sum(map(len,entries.values())),
        'schedule_endpoints_inspected':endpoints,'schedule_occurrences_admitted':admitted,
        'allocation_heap_offers':offers,'allocation_heap_pops':pops}
    return result
