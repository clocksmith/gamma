"""Fixed15-price supplied-input owner caps; no loader, optimizer or runner.

Unchanged57 baseline and a separate53 potential/index context are both charged.
Laminar group widths supply all-overlap multiplicity; start-order relaxation
visits every allowed owner arc for every fixed price. No edge graph is retained.
"""
import hashlib
import heapq
import importlib.util
import json
from pathlib import Path

_spec=importlib.util.spec_from_file_location('entry_price_parent57',Path(__file__).resolve().parents[1]/'owner-path-cap-v1/caps.py')
prior=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(prior)
parent=prior.parent
COMMON=('lambda_family','count_streams','price_caps','affine_envelopes','priced_prefixes',
        'one_owner_prefix','marginal_choices','shared_prefix','rows','deltas_vs57')
BASE57=('schema','owner_caps','owner_top_entries','owner_entry_counts','owner_prefixes','capped_prefixes',
        'one_owner_prefix','marginal_choices','shared_prefix','rows','deltas_vs53')
BASE53=('schema','lifted','tightened','new_only_class_counts','new_only_top_entries','digests','reductions','deltas')


def normalized(value):return json.loads(json.dumps(value,allow_nan=False))


def digest(value):
    # JSON normalization BEFORE sorting makes all inherited numeric-key maps
    # stable across retained JSON; new price dimensions are lists, not mappings.
    return hashlib.sha256(json.dumps(normalized(value),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def scientific57(base):
    return {**{key:base[key] for key in BASE57},'base':{key:base['base'][key] for key in BASE53}}


class DepthMap:
    """O(G+N) parent/terminal state, with one transient chain per suffix."""
    def __init__(self,index):
        groups=index.groups;N=len(index.positions)
        assert N and len(set(index.positions))==N
        assert len(index.remaining)==N
        for rank,(pid,start) in enumerate(index.positions):
            assert type(pid) is str and type(start) is int and 0<=start<len(index.texts[pid])
            assert index.remaining[rank]==len(index.texts[pid])-start
        self.groups=groups;self.parents=[-1]*len(groups);self.terminals=[None]*N
        self.ranks={position:rank for rank,position in enumerate(index.positions)}
        self.positions=index.positions;self.remaining=index.remaining
        order=sorted(range(len(groups)),key=lambda gid:(groups[gid]['lo'],-groups[gid]['hi']))
        assert len({(g['lo'],g['hi']) for g in groups})==len(groups)
        stack=[];starts={}
        for gid in order:
            g=groups[gid]
            assert all(type(g[key]) is int for key in ('lo','hi','first','last','multiplicity'))
            assert 0<=g['lo']<g['hi']<=N and 1<=g['first']<=g['last']
            excluded=g['excluded_lengths']
            assert type(excluded) is list and all(type(v) is int and g['first']<=v<=g['last'] for v in excluded)
            assert excluded==sorted(set(excluded))
            assert g['multiplicity']==g['last']-g['first']+1-len(excluded)
            while stack and g['lo']>=groups[stack[-1]]['hi']:stack.pop()
            if stack:
                outer=groups[stack[-1]]
                assert outer['lo']<=g['lo'] and g['hi']<=outer['hi'],'crossing intervals'
                assert g['first']==outer['last']+1,'depth gap or overlap'
                self.parents[gid]=stack[-1]
            else:assert g['first']==1,'root depth gap'
            starts.setdefault(g['lo'],[]).append(gid);stack.append(gid)
        # A genuine group may equal virtual root [0,N); it still has first1.
        active=[]
        for rank in range(N):
            while active and groups[active[-1]]['hi']<=rank:active.pop()
            for gid in starts.get(rank,[]):
                assert self.parents[gid]==(active[-1] if active else -1)
                active.append(gid)
            assert active,'uncovered suffix rank'
            terminal=active[-1]
            assert groups[terminal]['last']==index.remaining[rank],'source terminal depth mismatch'
            self.terminals[rank]=terminal

    def chain(self,pid,start):
        rank=self.ranks[pid,start];gid=self.terminals[rank];reverse=[]
        while gid!=-1:
            reverse.append(gid);gid=self.parents[gid]
            assert len(reverse)<=self.remaining[rank]
        chain=list(reversed(reverse));depth=1
        for gid in chain:
            g=self.groups[gid]
            assert g['lo']<=rank<g['hi'] and g['first']==depth
            depth=g['last']+1
        assert depth==self.remaining[rank]+1
        return chain


def allocate(prefixes,shared,L,D,capacity):
    frontier=[];totals=[0];choices=[];offers=pops=0
    for pid,values in sorted(prefixes.items()):
        if len(values)>1:
            heapq.heappush(frontier,(-(values[1]-values[0]),pid,1));offers+=1
    while frontier and len(choices)<capacity:
        negative,pid,rank=heapq.heappop(frontier);pops+=1
        choices.append((pid,rank,-negative));totals.append(totals[-1]-negative)
        values=prefixes[pid]
        if rank+1<len(values):
            gain=values[rank+1]-values[rank]
            assert 0<=gain<=-negative
            heapq.heappush(frontier,(-gain,pid,rank+1));offers+=1
    rows=[]
    for k in range(capacity+1):
        charge,negative=max((totals[j]+shared[min(capacity-j,len(shared)-1)],-j)
                            for j in range(min(k,len(totals)-1)+1))
        numerator=L-charge
        rows.append({'k':k,'charge':charge,'one_owner_slots':-negative,
            'shared_slots':min(capacity+negative,len(shared)-1),'numerator':numerator,
            'integer_lower_bound':-(-numerator//D)})
    return totals,choices,rows,offers,pops


def check(texts,banned,old_pool,old_q,seed,alphabet,D,*,expected_source_hashes,
          expected_old_banned,expected_old_certificate=None,
          expected_occurrence_sha256=None,capacity=256):
    if not __debug__:raise RuntimeError('normal assertions required')
    assert type(capacity) is int and capacity>=0
    same_bans=expected_old_banned is banned
    banned=set(banned)
    expected_old_banned=banned if same_bans else set(expected_old_banned)
    kwargs=dict(expected_source_hashes=expected_source_hashes,expected_old_banned=expected_old_banned,
        expected_old_certificate=expected_old_certificate,expected_occurrence_sha256=expected_occurrence_sha256)
    base=prior.check(texts,banned,old_pool,old_q,seed,alphabet,D,capacity=capacity,**kwargs)
    obj=parent.Tighten(texts,banned,old_pool,old_q,seed,alphabet,D,
        old_source_hashes=expected_source_hashes,old_banned=expected_old_banned,
        expected_old_certificate=expected_old_certificate,expected_occurrence_sha256=expected_occurrence_sha256)
    assert obj.path_numerators==base['base']['tightened']['path_numerators']
    assert obj.occurrence_sha256==base['base']['tightened']['occurrence_sha256']
    assert digest(obj.d)==base['base']['digests']['potentials_sha256']
    assert digest(obj.tight_weights)==base['base']['digests']['tightened_old_weights_sha256']
    prices=[0]+[D*(2**rank) for rank in range(14)];K=len(prices);assert K==15
    structure=DepthMap(obj.index)
    quotients={};schedules={};price_caps={};streams={}
    work={'baseline57_reconstructions':1,'additional53_contexts':1,'structural_groups':len(obj.index.groups),
        'terminal_positions_checked':len(obj.positions),'ancestor_group_visits':0,'candidate_owner_depths':0,
        'allowed_owner_endpoints':0,'banned_owner_endpoints':0,'multiplicity_cache_entries':0,
        'multiplicity_divisions':0,'q_evaluations':0,'price_residual_evaluations':0,
        'forward_arc_candidates':0,'forward_skip_candidates':0,'count_stream_records':0,
        'prefix_price_evaluations':0}
    for pid,text in sorted(texts.items()):
        vectors=[[0]*(len(text)+1) for _ in prices];d=obj.d[pid];source_stream=[]
        for start in range(len(text)):
            for values in vectors:
                values[start+1]=max(values[start+1],values[start]);work['forward_skip_candidates']+=1
            count_hash=hashlib.sha256();arcs=0
            for gid in structure.chain(pid,start):
                work['ancestor_group_visits']+=1;g=obj.index.groups[gid]
                if obj.support[gid]!=1:continue
                assert obj.positions[g['lo']][0]==pid
                m=g['hi']-g['lo'];assert m>0
                excluded=set(g['excluded_lengths'])
                for length in range(g['first'],g['last']+1):
                    end=start+length;work['candidate_owner_depths']+=1
                    assert (length in excluded)==(end in obj.index.banned_ends[pid][start])
                    if length in excluded:
                        work['banned_owner_endpoints']+=1;continue
                    if m not in quotients:
                        quotients[m]=[price//m for price in prices]
                        work['multiplicity_cache_entries']+=1;work['multiplicity_divisions']+=K
                    removed=quotients[m]
                    count_hash.update((f'[{end},{m}]\n').encode('ascii'));arcs+=1
                    q=max(0,d[start]-d[end]-(9 if length==1 else -1)*D)
                    work['q_evaluations']+=1
                    for values,amount in zip(vectors,removed):
                        residual=max(q-amount,0)
                        values[end]=max(values[end],values[start]+residual)
                        work['price_residual_evaluations']+=1;work['forward_arc_candidates']+=1
            work['allowed_owner_endpoints']+=arcs;work['count_stream_records']+=arcs
            source_stream.append({'arcs':arcs,'sha256':count_hash.hexdigest()})
        assert vectors[0]==base['owner_prefix_schedule'][pid]
        schedules[pid]=vectors;price_caps[pid]=[values[-1] for values in vectors];streams[pid]=source_stream
    expected=sum(g['multiplicity']*(g['hi']-g['lo']) for gid,g in enumerate(obj.index.groups) if obj.support[gid]==1)
    assert work['allowed_owner_endpoints']==expected==base['work']['schedule_one_owner_occurrences']
    assert work['ancestor_group_visits']<=sum(len(t)*(len(t)+1)//2 for t in texts.values())
    assert work['candidate_owner_depths']==work['allowed_owner_endpoints']+work['banned_owner_endpoints']
    assert work['price_residual_evaluations']==work['forward_arc_candidates']==K*expected
    envelopes={};prefixes={}
    for pid,values in base['owner_prefixes'].items():
        envelope=[min(price*t+cap for price,cap in zip(prices,price_caps[pid])) for t in range(len(values))]
        work['prefix_price_evaluations']+=K*len(values)
        prefix=[min(weight,line) for weight,line in zip(values,envelope)]
        increments=[b-a for a,b in zip(prefix,prefix[1:])]
        assert prefix[0]==0 and all(v>=0 for v in increments)
        assert all(a>=b for a,b in zip(increments,increments[1:]))
        assert all(a<=b for a,b in zip(prefix,base['capped_prefixes'][pid]))
        assert len(prefix)==min(capacity,base['owner_entry_counts'][pid])+1
        envelopes[pid]=envelope;prefixes[pid]=prefix
    one,choices,rows,offers,pops=allocate(prefixes,base['shared_prefix'],sum(obj.path_numerators.values()),D,capacity)
    work.update(allocation_heap_offers=offers,allocation_heap_pops=pops)
    deltas=[]
    for row,old in zip(rows,base['rows']):
        assert row['charge']<=old['charge']
        deltas.append({'k':row['k'],'charge_reduction':old['charge']-row['charge'],
            'integer_bound_gain':row['integer_lower_bound']-old['integer_lower_bound']})
    result={'schema':'gamma.entry-price-path-cap.supplied.v1','base57':base,'lambda_family':prices,
        'count_streams':streams,'price_caps':price_caps,'price_prefix_schedule':schedules,
        'affine_envelopes':envelopes,'priced_prefixes':prefixes,'one_owner_prefix':one,
        'marginal_choices':choices,'shared_prefix':base['shared_prefix'],'rows':rows,'deltas_vs57':deltas}
    result['digests']={key+'_sha256':digest(result[key]) for key in COMMON+('price_prefix_schedule',)}
    result['digests']['base57_sha256']=digest(scientific57(base))
    result['work']=work
    return result
