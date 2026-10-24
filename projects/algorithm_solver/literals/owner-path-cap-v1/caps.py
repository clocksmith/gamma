"""In-memory owner-cap production prototype; no loader or corpus runner.

Shares unchanged item53 reconstruction and its paired baseline certificate.
New owner-specific lists and forward schedules are independently replayed by
this item's separate checker. No global top list substitutes for owner lists.
"""
import heapq
import importlib.util
from pathlib import Path

_spec=importlib.util.spec_from_file_location('owner_cap_parent53',Path(__file__).resolve().parents[1]/'potential-tightening-v1/tighten.py')
parent=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(parent)


def prefix(entries):
    result=[0]
    for weight,*_ in entries:result.append(result[-1]+weight)
    return result


def allocate(owner_entries,caps,shared_entries,total,D,capacity):
    owner_prefixes={pid:prefix(entries) for pid,entries in owner_entries.items()}
    capped={pid:[min(value,caps[pid]) for value in values] for pid,values in owner_prefixes.items()}
    frontier=[]
    for pid,values in capped.items():
        assert values[0]==0
        increments=[b-a for a,b in zip(values,values[1:])]
        assert increments==sorted(increments,reverse=True) and all(v>=0 for v in increments)
        if increments:heapq.heappush(frontier,(-increments[0],pid,1))
    choices=[];one=[0]
    while frontier and len(choices)<capacity:
        negative,pid,rank=heapq.heappop(frontier)
        choices.append((pid,rank,-negative));one.append(one[-1]-negative)
        values=capped[pid]
        if rank+1<len(values):heapq.heappush(frontier,(-(values[rank+1]-values[rank]),pid,rank+1))
    shared=prefix(shared_entries);rows=[]
    for k in range(capacity+1):
        charge,negative_one,shared_slots=max(
            (one[j]+shared[min(capacity-j,len(shared)-1)],-j,min(capacity-j,len(shared)-1))
            for j in range(min(k,len(one)-1)+1))
        numerator=total-charge
        rows.append({'k':k,'charge':charge,'one_owner_slots':-negative_one,
                     'shared_slots':shared_slots,'numerator':numerator,
                     'integer_lower_bound':-(-numerator//D)})
    return owner_prefixes,capped,one,choices,shared,rows


def check(texts,banned,old_pool,old_q,seed,alphabet,D,*,expected_source_hashes,
          expected_old_banned,expected_old_certificate=None,
          expected_occurrence_sha256=None,capacity=256):
    if not __debug__:raise RuntimeError('normal assertions required')
    assert type(capacity) is int and capacity>=0
    obj=parent.Tighten(texts,banned,old_pool,old_q,seed,alphabet,D,
        old_source_hashes=expected_source_hashes,old_banned=expected_old_banned,
        expected_old_certificate=expected_old_certificate,
        expected_occurrence_sha256=expected_occurrence_sha256)
    base=obj.certificate(capacity)
    owner_top={pid:parent.Top(capacity) for pid in sorted(texts)}
    counts={pid:0 for pid in sorted(texts)}
    overrides={}
    for (gid,length),eid in obj.old_entry_ids.items():
        overrides.setdefault(gid,set()).add(length)
        if obj.support[gid]==1:
            pid,_=obj.positions[obj.index.groups[gid]['lo']]
            owner_top[pid].add(obj.tight_weights[eid],gid,length)
    minima={pid:parent.Minimum(d) for pid,d in obj.d.items()}
    unique={pid:[] for pid in sorted(texts)}
    queries=0;repeated_work=0;extracted=0
    shared_depth={pid:[0]*len(text) for pid,text in texts.items()}
    expected_arcs=0

    def add_range(gid,pid,start,first,last):
        nonlocal queries
        if first>last:return
        assert first>=2,'all occurring singletons are old'
        value,end=minima[pid].query(start+first,start+last+1);queries+=1
        weight=max(0,obj.d[pid][start]+D-value)
        length=end-start if weight else first
        heapq.heappush(unique[pid],(-weight,gid,length,start,first,last))

    for gid,group in enumerate(obj.index.groups):
        if obj.support[gid]==2:
            # Ownership is defined before bans; banned shared depths still
            # delimit the first possible one-owner prefix at each position.
            for pid,start in obj.positions[group['lo']:group['hi']]:
                shared_depth[pid][start]=max(shared_depth[pid][start],group['last'])
            continue
        positions=obj.positions[group['lo']:group['hi']]
        pid=positions[0][0];assert all(owner==pid for owner,_ in positions)
        counts[pid]+=group['multiplicity']
        expected_arcs+=group['multiplicity']*len(positions)
        excluded=set(group['excluded_lengths'])|overrides.get(gid,set())
        if len(positions)==1:
            _,start=positions[0];first=group['first']
            for length in sorted(excluded):
                add_range(gid,pid,start,first,length-1);first=length+1
            add_range(gid,pid,start,first,group['last'])
        else:
            for length in range(group['first'],group['last']+1):
                if length in excluded:continue
                assert length>=2
                weight=0
                for _,start in positions:
                    weight+=max(0,obj.d[pid][start]-obj.d[pid][start+length]+D)
                    repeated_work+=1
                owner_top[pid].add(weight,gid,length)
    for pid,frontier in unique.items():
        for _ in range(capacity):
            if not frontier:break
            negative,gid,length,start,first,last=heapq.heappop(frontier)
            owner_top[pid].add(-negative,gid,length);extracted+=1
            add_range(gid,pid,start,first,length-1)
            add_range(gid,pid,start,length+1,last)
    entries={pid:top.entries() for pid,top in owner_top.items()}
    assert all(len(entries[pid])==min(capacity,counts[pid]) for pid in texts)
    assert sum(counts.values())==base['tightened']['class_counts'][1]
    # Owner tops must reproduce the old global top, without using it to select.
    global_top=parent.Top(capacity)
    for items in entries.values():
        for item in items:global_top.add(*item)
    assert global_top.entries()==base['tightened']['top_entries'][1]
    schedules={};caps={};inspected=0;admitted=0
    for pid,text in sorted(texts.items()):
        values=[0]*(len(text)+1);distance=obj.d[pid]
        for end in range(1,len(text)+1):
            best=values[end-1]
            for start in range(end):
                inspected+=1;length=end-start
                if length<=shared_depth[pid][start] or end in obj.index.banned_ends[pid][start]:continue
                admitted+=1
                q=max(0,distance[start]-distance[end]-(9 if length==1 else -1)*D)
                best=max(best,values[start]+q)
            values[end]=best
        schedules[pid]=values;caps[pid]=values[-1]
    assert admitted==expected_arcs
    shared=base['tightened']['top_entries'][2]
    total=sum(obj.path_numerators.values())
    op,cp,one,choices,sp,rows=allocate(entries,caps,shared,total,D,capacity)
    deltas=[]
    for old,new in zip(base['tightened']['rows'],rows):
        assert old['k']==new['k'] and new['charge']<=old['charge']
        deltas.append({'k':new['k'],'charge_reduction':old['charge']-new['charge'],
                       'integer_bound_gain':new['integer_lower_bound']-old['integer_lower_bound']})
    proof={'schema':'gamma.owner-path-cap.supplied.v1','base':base,'owner_caps':caps,'owner_top_entries':entries,
        'owner_entry_counts':counts,'owner_prefixes':op,'capped_prefixes':cp,
        'owner_prefix_schedule':schedules,'one_owner_prefix':one,'marginal_choices':choices,
        'shared_prefix':sp,'rows':rows,'deltas_vs53':deltas}
    proof['digests']={key+'_sha256':parent.digest(proof[key]) for key in
        ('owner_caps','owner_top_entries','owner_entry_counts','owner_prefixes','capped_prefixes',
         'owner_prefix_schedule','one_owner_prefix','marginal_choices','shared_prefix','rows','deltas_vs53')}
    proof['digests']['base_paired_sha256']=parent.digest({key:base[key] for key in
        ('lifted','tightened','new_only_class_counts','new_only_top_entries','digests','reductions','deltas')})
    proof['work']={'owner_unique_range_queries':queries,'owner_unique_entries_extracted':extracted,
        'repeated_new_occurrence_contributions':repeated_work,'schedule_endpoints_inspected':inspected,
        'schedule_one_owner_occurrences':admitted,'shared_prefix_positions':sum(map(len,shared_depth.values()))}
    return proof
