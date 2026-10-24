"""Item62 pure supplied-prefix allocation; no source or corpus reader.

Heap and owner-scan implementations reconstruct both parent numerical curves.
Shape checks do not establish source ownership, shared identities, reachability
or weight provenance; those remain supplied scientific authority. No frozen
production helper is imported and no precomputed parent row is trusted.

API: heap(...) and scan(...) accept owner_prefixes, capped_prefixes,
local_shared_prefixes, all_caps, shared_prefix, sorted forced_owners, L, D and
capacity (default256). Every prefix starts at zero and contains only real
entries, truncated at capacity; its length determines finite available slots.
All local shared prefixes have the same length as the global shared prefix.
At capacity0, [0] is truncation rather than proof that an owner has no entries;
a nonempty supplied forced set still proves empty budgets without reading rank1.
For positive capacity each forced owner must expose a real first prefix entry.
The capped endpoint verifies min(A[t], endpoint), not the unobserved true Rone.
Allocation methods share validation/formula/row construction, but heap and scan
choose residual marginals separately. Oracle tests check the shared formula.
Only O(P+B squared) allocation state is retained, not a split-by-owner-by-rank
function matrix; retained input prefixes themselves occupy O(PB) values.
"""
import hashlib
import heapq
import json


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def prefix_check(values,capacity):
    assert type(values) is list and 1<=len(values)<=capacity+1
    assert all(type(value) is int and value>=0 for value in values) and values[0]==0
    increments=[b-a for a,b in zip(values,values[1:])]
    assert all(value>=0 for value in increments)
    assert all(a>=b for a,b in zip(increments,increments[1:]))


def validate(owner_prefixes,capped_prefixes,local_shared_prefixes,all_caps,shared_prefix,forced_owners,L,D,capacity):
    if not __debug__:raise RuntimeError('normal assertions required')
    assert type(capacity) is int and 0<=capacity<=256
    assert type(L) is int and type(D) is int and D>0
    assert type(owner_prefixes) is dict and owner_prefixes and all(type(pid) is str for pid in owner_prefixes)
    keys=owner_prefixes.keys()
    for mapping in (capped_prefixes,local_shared_prefixes,all_caps):
        assert type(mapping) is dict and mapping.keys()==keys
    assert type(forced_owners) is list and all(type(pid) is str for pid in forced_owners)
    assert forced_owners==sorted(set(forced_owners)) and set(forced_owners)<=keys
    prefix_check(shared_prefix,capacity)
    for pid,values in owner_prefixes.items():
        prefix_check(values,capacity);prefix_check(capped_prefixes[pid],capacity)
        assert len(values)==len(capped_prefixes[pid])
        cap=capped_prefixes[pid][-1]
        assert capped_prefixes[pid]==[min(value,cap) for value in values]
        assert type(all_caps[pid]) is int and all_caps[pid]>=cap
        local=local_shared_prefixes[pid];prefix_check(local,capacity)
        assert len(local)==len(shared_prefix)
        assert all(a<=b for a,b in zip(local,shared_prefix))
    # B=0 truncates every prefix before its first real entry. Emptiness still
    # follows from the supplied required set; no truncated entry is inspected.
    if capacity:
        assert all(len(owner_prefixes[pid])>=2 for pid in forced_owners)


def curve_heap(lengths,value,forced,limit,work):
    r=len(forced)
    if r>limit:return {},[]
    required=set(forced);used={pid:int(pid in required) for pid in lengths}
    assert all(used[pid]<lengths[pid] for pid in lengths)
    baseline=sum(value(pid,rank) for pid,rank in used.items())
    frontier=[];choices=[];totals={r:baseline}
    def offer(pid,rank,prior=None):
        marginal=value(pid,rank)-value(pid,rank-1)
        assert marginal>=0 and (prior is None or marginal<=prior)
        heapq.heappush(frontier,(-marginal,pid,rank));work['heap_offers']+=1
    for pid in sorted(lengths):
        if used[pid]+1<lengths[pid]:offer(pid,used[pid]+1)
    for count in range(r+1,limit+1):
        if not frontier:break
        negative,pid,rank=heapq.heappop(frontier);work['heap_pops']+=1
        assert rank==used[pid]+1;used[pid]=rank
        choices.append((pid,rank,-negative));totals[count]=totals[count-1]-negative
        if rank+1<lengths[pid]:offer(pid,rank+1,-negative)
    return totals,choices


def curve_scan(lengths,value,forced,limit,work):
    """Separate allocation traversal: scan each owner's next residual rank."""
    first=len(forced)
    if first>limit:return {},[]
    counts={pid:1 if pid in forced else 0 for pid in lengths}
    assert all(counts[pid]<lengths[pid] for pid in lengths)
    totals={first:sum(value(pid,counts[pid]) for pid in lengths)};choices=[]
    for step in range(first+1,limit+1):
        best=None
        for pid in sorted(lengths):
            work['owner_scan_visits']+=1
            rank=counts[pid]+1
            if rank>=lengths[pid]:continue
            gain=value(pid,rank)-value(pid,rank-1);assert gain>=0
            candidate=(-gain,pid,rank)
            if best is None or candidate<best:best=candidate
        if best is None:break
        negative,pid,rank=best;counts[pid]=rank
        choices.append((pid,rank,-negative));totals[step]=totals[step-1]-negative
    return totals,choices


def rows_from_splits(splits,capacity,L,D,field,floor):
    rows=[];best=None
    by_j={row['one_owner_slots']:row for row in splits}
    for k in range(capacity+1):
        if k<floor:
            rows.append({'k':k,'empty_by_required_owners':True,'one_owner_slots':None,
                'shared_slots':None,'charge':None,'numerator':None,'integer_lower_bound':None})
            continue
        row=by_j.get(k)
        if row is not None and row[field] is not None and (best is None or row[field]>best[field]):best=row
        assert best is not None
        numerator=L-best[field]
        rows.append({'k':k,'empty_by_required_owners':False,'one_owner_slots':best['one_owner_slots'],
            'shared_slots':best['shared_slots_available'],'charge':best[field],'numerator':numerator,
            'integer_lower_bound':-(-numerator//D)})
    return rows


def allocate(owner_prefixes,capped_prefixes,local_shared_prefixes,all_caps,shared_prefix,
             forced_owners,L,D,capacity=256,*,method='heap'):
    validate(owner_prefixes,capped_prefixes,local_shared_prefixes,all_caps,shared_prefix,forced_owners,L,D,capacity)
    assert method in ('heap','scan')
    curve=curve_heap if method=='heap' else curve_scan
    work={'heap_offers':0,'heap_pops':0,'owner_scan_visits':0,'joint_splits':0}
    lengths={pid:len(values) for pid,values in owner_prefixes.items()};r=len(forced_owners)
    limit=min(capacity,sum(length-1 for length in lengths.values()))
    owner_value=lambda pid,rank:capped_prefixes[pid][rank]
    owner57,choices57=curve(lengths,owner_value,[],limit,work)
    owner61,choices61=curve(lengths,owner_value,forced_owners,limit,work)
    splits=[]
    for j in range(limit+1):
        work['joint_splits']+=1;s=capacity-j;available=min(s,len(shared_prefix)-1)
        offsets={pid:values[available] for pid,values in local_shared_prefixes.items()}
        value=lambda pid,rank:min(offsets[pid]+owner_prefixes[pid][rank],all_caps[pid])
        unconstrained,unconstrained_choices=curve(lengths,value,[],j,work)
        required,required_choices=curve(lengths,value,forced_owners,j,work)
        zero=sum(value(pid,0) for pid in lengths)
        joint60=unconstrained[j];prior57=shared_prefix[available]+owner57[j]
        joint62=required.get(j)
        prior61=shared_prefix[available]+owner61[j] if j in owner61 else None
        mandatory=required[r] if required else None
        assert (joint62 is None)==(j<r)==(prior61 is None)
        if j>=r:
            assert joint62<=joint60 and prior61<=prior57
        splits.append({'one_owner_slots':j,'shared_slots':s,'shared_slots_available':available,
            'zero_baseline':zero,'mandatory_baseline':mandatory,
            'mandatory_increment':None if mandatory is None else mandatory-zero,
            'joint60_charge':joint60,'prior57_charge':prior57,'charge60':min(joint60,prior57),
            'joint62_charge':joint62,'charge61':prior61,
            'charge62':None if joint62 is None else min(joint62,prior61),
            'unconstrained_choices':unconstrained_choices,'required_choices':required_choices})
    rows60=rows_from_splits(splits,capacity,L,D,'charge60',0)
    rows61=rows_from_splits(splits,capacity,L,D,'charge61',r)
    rows=rows_from_splits(splits,capacity,L,D,'charge62',r)
    for row,old60,old61 in zip(rows,rows60,rows61):
        if row['empty_by_required_owners']:
            row.update(charge_reduction_vs60=None,charge_reduction_vs61=None,
                integer_gain_vs60=None,integer_gain_vs61=None)
        else:
            assert row['charge']<=old60['charge'] and row['charge']<=old61['charge']
            row.update(charge_reduction_vs60=old60['charge']-row['charge'],
                charge_reduction_vs61=old61['charge']-row['charge'],
                integer_gain_vs60=row['integer_lower_bound']-old60['integer_lower_bound'],
                integer_gain_vs61=row['integer_lower_bound']-old61['integer_lower_bound'])
    result={'schema':'gamma.required-joint-path-cap.allocation.v1','coverage_floor':r,
        'owner57_prefix':owner57,'owner61_prefix':owner61,'owner57_choices':choices57,'owner61_choices':choices61,
        'split_rows':splits,'parent60_rows':rows60,'parent61_rows':rows61,'rows':rows}
    result['digests']={key+'_sha256':digest(result[key]) for key in
        ('owner57_prefix','owner61_prefix','owner57_choices','owner61_choices','split_rows','parent60_rows','parent61_rows','rows')}
    result['work']=work
    return result


def heap(*args,**kwargs):return allocate(*args,**kwargs,method='heap')
def scan(*args,**kwargs):return allocate(*args,**kwargs,method='scan')
