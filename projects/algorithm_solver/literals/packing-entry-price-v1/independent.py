"""Item71 owner-packing checker with fresh AC/Z counts and backward schedules.

Unchanged63 independent baseline is explicit. Additional old q/potentials and
all owner counts are reconstructed here; no production Tighten/DepthMap import.
"""
from collections import deque
import hashlib
import importlib.util
import json
import math
from pathlib import Path
_spec=importlib.util.spec_from_file_location('packing71_independent_base63',Path(__file__).resolve().parents[1]/'entry-price-path-cap-v1/independent.py')
prior=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(prior)
parent=prior.parent
COMMON_FIELDS=('lambda_family','count_streams','price_caps','affine_envelopes','priced_prefixes',
    'one_owner_prefix','marginal_choices','shared_prefix','rows','deltas_vs63','deltas_vs57','packing_diagnostics')


def normalized(value):
    if type(value) is dict:
        assert all(type(k) in (str,int) for k in value)
        out={str(k):normalized(v) for k,v in value.items()};assert len(out)==len(value);return out
    if type(value) in (tuple,list):return [normalized(v) for v in value]
    assert type(value) in (str,int,bool,float,type(None))
    if type(value) is float:assert math.isfinite(value)
    return value


def digest(value):
    return hashlib.sha256(json.dumps(normalized(value),sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()


def scientific63(value):
    return prior.scientific(value)


def scientific(value):
    return {'schema':value['schema'],'base63':scientific63(value['base63']),**{key:value[key] for key in COMMON_FIELDS}}


def verify_base63(supplied,checked,texts,B):
    """Exact old scientific/vector commitments; only checkable work identities.

    Independent AC/Z counters intentionally differ from production traversal.
    This is not an assertion of equality between the two work dictionaries.
    """
    assert set(supplied)=={'schema','base57','digests','work','price_prefix_schedule',*prior.COMMON_FIELDS}
    assert digest(scientific63(supplied))==digest(scientific63(checked))
    expected={key+'_sha256':digest(supplied[key]) for key in (*prior.COMMON_FIELDS,'price_prefix_schedule')}
    expected['base57_sha256']=digest(prior.scientific57(supplied['base57']))
    assert supplied['digests']==expected
    assert checked['production_forward_schedule_checked'] is True
    assert checked['production_forward_schedule_sha256']==expected['price_prefix_schedule_sha256']
    old57=supplied['base57'];checked57=checked['base57']
    keys=('owner_caps','owner_top_entries','owner_entry_counts','owner_prefixes','capped_prefixes',
          'owner_prefix_schedule','one_owner_prefix','marginal_choices','shared_prefix','rows','deltas_vs53')
    expected57={key+'_sha256':digest(old57[key]) for key in keys}
    expected57['base_paired_sha256']=digest({key:old57['base'][key] for key in
        ('lifted','tightened','new_only_class_counts','new_only_top_entries','digests','reductions','deltas')})
    assert old57['digests']==expected57
    assert checked57['production_forward_schedule_checked'] is True
    assert checked57['production_forward_schedule_sha256']==digest(old57['owner_prefix_schedule'])
    w=supplied['work'];cw=checked['work'];N=sum(map(len,texts.values()));A=cw['one_owner_occurrences'];K=15
    assert set(w)=={'baseline57_reconstructions','additional53_contexts','structural_groups',
        'terminal_positions_checked','ancestor_group_visits','candidate_owner_depths',
        'allowed_owner_endpoints','banned_owner_endpoints','multiplicity_cache_entries','multiplicity_divisions',
        'q_evaluations','price_residual_evaluations','forward_arc_candidates','forward_skip_candidates',
        'count_stream_records','prefix_price_evaluations','allocation_heap_offers','allocation_heap_pops'}
    assert all(type(v) is int and v>=0 for v in w.values())
    assert w['baseline57_reconstructions']==w['additional53_contexts']==1
    assert w['structural_groups']==cw['support_groups_classified']
    assert w['terminal_positions_checked']==N
    assert w['ancestor_group_visits']<=cw['endpoints_inspected']
    assert w['candidate_owner_depths']==A+w['banned_owner_endpoints']<=cw['endpoints_inspected']
    assert w['banned_owner_endpoints']<=cw['banned_endpoints_skipped']
    assert w['allowed_owner_endpoints']==w['count_stream_records']==w['q_evaluations']==A
    assert w['multiplicity_cache_entries']<=w['structural_groups']
    assert w['multiplicity_divisions']==K*w['multiplicity_cache_entries']
    assert w['price_residual_evaluations']==w['forward_arc_candidates']==K*A
    assert w['forward_skip_candidates']==K*N
    assert w['prefix_price_evaluations']==cw['prefix_price_evaluations']
    assert w['allocation_heap_pops']==len(supplied['marginal_choices'])<=B
    offers=sum(len(v)>1 for v in supplied['priced_prefixes'].values())
    offers+=sum(rank+1<len(supplied['priced_prefixes'][pid]) for pid,rank,_ in supplied['marginal_choices'])
    assert w['allocation_heap_offers']==offers
    oldwork=old57['work']
    assert all(type(v) is int and v>=0 for v in oldwork.values())
    assert oldwork['schedule_one_owner_occurrences']==A
    assert oldwork['shared_prefix_positions']==N


class AC:
    """Fresh terminal-link matcher; emits ends in order, without output copying."""
    def __init__(self, words):
        self.words = words
        self.children, self.fail, self.hit, self.link = [{}], [0], [None], [None]
        for eid, word in enumerate(words):
            node = 0
            for ch in word:
                if ch not in self.children[node]:
                    self.children[node][ch] = len(self.children)
                    self.children.append({}); self.fail.append(0)
                    self.hit.append(None); self.link.append(None)
                node = self.children[node][ch]
            assert self.hit[node] is None
            self.hit[node] = eid
        queue = deque(self.children[0].values())
        while queue:
            node = queue.popleft()
            for ch, child in self.children[node].items():
                fallback = self.fail[node]
                while fallback and ch not in self.children[fallback]: fallback = self.fail[fallback]
                target = self.children[fallback].get(ch,0)
                self.fail[child] = target
                self.link[child] = target if self.hit[target] is not None else self.link[target]
                queue.append(child)

    def matches(self, text):
        node = 0
        for end, ch in enumerate(text,1):
            while node and ch not in self.children[node]: node = self.fail[node]
            node = self.children[node].get(ch,0)
            hit = node if self.hit[node] is not None else self.link[node]
            while hit is not None:
                eid = self.hit[hit]
                yield end-len(self.words[eid]),end,eid
                hit = self.link[hit]


def check(texts,banned,old_pool,old_q,seed,alphabet,D,*,expected_source_hashes,
          expected_old_banned,expected_old_certificate=None,expected_occurrence_sha256=None,
          capacity=256,expected_base57_prefix_schedule=None,expected_price_prefix_schedule=None,
          expected_count_streams=None,expected_price_caps=None,expected_base63=None,
          expected_packing_diagnostics=None,expected_priced_prefixes=None):
    if not __debug__:raise RuntimeError('normal assertions required')
    same_bans=banned is expected_old_banned
    banned=set(banned)
    expected_old_banned=banned if same_bans else set(expected_old_banned)
    old_kwargs={}
    if expected_base63 is not None:
        assert type(expected_base63) is dict
        old_kwargs={'expected_price_prefix_schedule':expected_base63['price_prefix_schedule'],
                    'expected_count_streams':expected_base63['count_streams'],
                    'expected_price_caps':expected_base63['price_caps']}
        old57=expected_base63['base57']['owner_prefix_schedule']
        if expected_base57_prefix_schedule is not None:
            assert normalized(old57)==normalized(expected_base57_prefix_schedule)
        expected_base57_prefix_schedule=old57
    base63=prior.check(texts,banned,old_pool,old_q,seed,alphabet,D,
        expected_source_hashes=expected_source_hashes,expected_old_banned=expected_old_banned,
        expected_old_certificate=expected_old_certificate,expected_occurrence_sha256=expected_occurrence_sha256,
        capacity=capacity,expected_base57_prefix_schedule=expected_base57_prefix_schedule,**old_kwargs)
    if expected_base63 is not None:verify_base63(expected_base63,base63,texts,capacity)
    base57=base63['base57']
    index = parent.full.Index(texts,set(banned))
    parent.full.verify(index,{pid:[0]*len(t) for pid,t in texts.items()},0,1)
    positions = index.positions
    ranks = {position:rank for rank,position in enumerate(positions)}
    groups = {(g['lo'],g['hi']):gid for gid,g in enumerate(index.groups)}
    assert len(groups) == len(index.groups)
    # A suffix interval is one-owner iff it ends inside this same-owner run.
    # Only the 1 / at-least-2 classification is needed, not distinct counts.
    run_end = [0]*len(positions)
    for rank in range(len(positions)-1,-1,-1):
        run_end[rank] = (run_end[rank+1] if rank+1<len(positions) and
                         positions[rank][0]==positions[rank+1][0] else rank+1)
    supports = [1 if g['hi']<=run_end[g['lo']] else 2 for g in index.groups]
    matcher = AC(old_pool)
    owners = [set() for _ in old_pool]
    occurrences = [0]*len(old_pool)
    lows, highs = [len(positions)]*len(old_pool), [-1]*len(old_pool)
    weights = [0]*len(old_pool)
    potentials = {}; cursor = 0; occurrence_hash = hashlib.sha256(); bellman = 0
    for pid,text in sorted(texts.items()):
        outgoing = [[] for _ in text]
        for start,end,eid in matcher.matches(text): outgoing[start].append((end,eid))
        incoming = [[] for _ in range(len(text)+1)]
        for start,matches in enumerate(outgoing):
            assert matches == sorted(matches)
            for end,eid in matches:
                assert cursor < len(old_q)
                q = old_q[cursor]; cursor += 1
                occurrence_hash.update((json.dumps([pid,start,end,eid],separators=(',',':'))+'\n').encode())
                incoming[end].append((start,(9 if end-start==1 else -1)*D+q))
                weights[eid] += q; owners[eid].add(pid); occurrences[eid] += 1
                rank = ranks[pid,start]; lows[eid]=min(lows[eid],rank); highs[eid]=max(highs[eid],rank)
        d = [None]*len(text)+[0]
        for end in range(len(text),0,-1):
            assert d[end] is not None
            for start,cost in incoming[end]:
                value = d[end]+cost
                if d[start] is None or value < d[start]: d[start]=value
        assert all(type(v) is int for v in d)
        for end,edges in enumerate(incoming):
            for start,cost in edges:
                assert d[start] <= d[end]+cost; bellman += 1
        assert d[0] == base57['base']['tightened']['path_numerators'][pid]
        potentials[pid] = d
    assert cursor == len(old_q) == base57['base']['tightened']['old_occurrences']
    assert occurrence_hash.hexdigest() == base57['base']['tightened']['occurrence_sha256']
    assert digest(potentials) == base57['base']['digests']['potentials_sha256']
    assert digest(weights) == base57['base']['digests']['old_weights_sha256']

    identities = {}; mapped_shared = dict.fromkeys(range(len(index.groups)),0)
    for eid,word in enumerate(old_pool):
        if not occurrences[eid]: continue
        assert highs[eid]-lows[eid]+1 == occurrences[eid]
        gid = groups[lows[eid],highs[eid]+1]; g=index.groups[gid]; length=len(word)
        assert g['first'] <= length <= g['last'] and length not in g['excluded_lengths']
        assert supports[gid] == min(2,len(owners[eid]))
        if len(owners[eid]) >= 2:
            assert (gid,length) not in identities
            identities[gid,length] = eid; mapped_shared[gid] += 1
    for gid,g in enumerate(index.groups):
        if supports[gid] >= 2: assert mapped_shared[gid] == g['multiplicity'], 'missing allowed shared identity'
    prices=[0]+[D*2**r for r in range(14)]
    assert len(prices)==15 and prices==sorted(set(prices))
    if expected_price_prefix_schedule is not None:
        assert type(expected_price_prefix_schedule) is dict and expected_price_prefix_schedule.keys()==texts.keys()
        for pid,text in texts.items():
            vectors=expected_price_prefix_schedule[pid]
            assert type(vectors) is list and len(vectors)==len(prices)
            for vector in vectors:
                assert type(vector) is list and len(vector)==len(text)+1 and vector[0]==0
                assert all(type(v) is int and v>=0 for v in vector)
    # Only all allowed shared entries establish the owner threshold. They were
    # independently proved complete above; banned depths are separately skipped.
    count_streams={};price_caps={};suffixes={}
    z_symbols=z_comparisons=z_histogram_cells=0
    reduced=max_m=max_n=reductions=0
    ac_replayed=old_owned_checked=endpoints=banned_skips=shared_skips=admitted=0
    backward_candidates=forward_candidates=forward_positions=0
    ban_matcher=AC(sorted(banned));banned_occurrences=0
    for pid,text in sorted(texts.items()):
        n=len(text);codes=list(map(ord,text));shared_depth=[0]*n;old_owned=[{} for _ in text]
        for start,end,eid in matcher.matches(text):
            ac_replayed+=1
            if len(owners[eid])>=2:shared_depth[start]=max(shared_depth[start],end-start)
            else:
                assert owners[eid]=={pid};old_owned[start][end]=eid
        bans=[set() for _ in text]
        for start,end,_ in ban_matcher.matches(text):bans[start].add(end);banned_occurrences+=1
        assert bans==index.banned_ends[pid]
        backward=[[0]*(n+1) for _ in prices]
        if expected_price_prefix_schedule is not None:
            supplied=expected_price_prefix_schedule[pid]
            audit=[[0]+vector[:-1] for vector in supplied]
        streams=[None]*n;d=potentials[pid]
        for start in range(n-1,-1,-1):
            multiplicities,work=z_counts(codes,start)
            z_symbols+=work['symbols'];z_comparisons+=work['comparisons'];z_histogram_cells+=work['histogram_cells']
            stream=hashlib.sha256();arcs=0
            for a in range(len(prices)):backward[a][start]=backward[a][start+1]
            for end in range(start+1,n+1):
                endpoints+=1;length=end-start
                if end in bans[start]:banned_skips+=1;continue
                if length<=shared_depth[start]:shared_skips+=1;continue
                count=multiplicities[length];assert type(count) is int and 1<=count<=n
                if end in old_owned[start]:
                    eid=old_owned[start][end];assert count==occurrences[eid];old_owned_checked+=1
                packed=min(count,n//length);assert 1<=packed<=count
                max_m=max(max_m,count);max_n=max(max_n,packed)
                reduced+=int(packed<count);reductions+=count-packed
                stream.update((json.dumps([end,count,packed],separators=(',',':'))+'\n').encode('ascii'))
                arcs+=1;admitted+=1
                penalty=max(0,d[start]-d[end]-(9 if length==1 else -1)*D)
                for a,price in enumerate(prices):
                    residual=max(0,penalty-price//packed)
                    assert residual<=max(0,penalty-price//count)
                    backward[a][start]=max(backward[a][start],residual+backward[a][end]);backward_candidates+=1
                    if expected_price_prefix_schedule is not None:
                        audit[a][end]=max(audit[a][end],supplied[a][start]+residual);forward_candidates+=1
            streams[start]={'arcs':arcs,'sha256':stream.hexdigest()}
        caps=[vector[0] for vector in backward]
        assert backward[0]==base57['owner_suffix_schedule'][pid]
        assert caps[0]==base57['owner_caps'][pid]
        assert backward[0]==base63['price_suffix_schedule'][pid][0]
        assert all(new<=old for new,old in zip(caps,base63['price_caps'][pid]))
        assert all(new<=old for a in range(len(prices))
                   for new,old in zip(backward[a],base63['price_suffix_schedule'][pid][a]))
        if expected_price_prefix_schedule is not None:
            for a in range(len(prices)):
                assert audit[a]==supplied[a],('price forward recurrence',pid,a)
                assert supplied[a][-1]==caps[a]
                forward_positions+=n
        count_streams[pid]=streams;price_caps[pid]=caps;suffixes[pid]=backward
    assert ac_replayed==cursor
    assert old_owned_checked==sum(occurrences[eid] for eid in range(len(old_pool)) if len(owners[eid])==1)
    expected_arcs=sum((g['hi']-g['lo'])*g['multiplicity'] for gid,g in enumerate(index.groups) if supports[gid]==1)
    assert admitted==expected_arcs and endpoints==sum(len(t)*(len(t)+1)//2 for t in texts.values())
    assert banned_skips==sum(len(ends) for rows in index.banned_ends.values() for ends in rows)
    if expected_count_streams is not None:assert normalized(expected_count_streams)==count_streams and digest(expected_count_streams)==digest(count_streams)
    if expected_price_caps is not None:
        assert type(expected_price_caps) is dict and expected_price_caps.keys()==price_caps.keys()
        for values in expected_price_caps.values():assert type(values) is list and all(type(v) is int for v in values)
        assert expected_price_caps==price_caps
    allocated=allocate(base57,prices,price_caps,capacity,D)
    for pid,values in allocated['priced_prefixes'].items():
        assert len(values)==len(base63['priced_prefixes'][pid])
        assert all(a<=b for a,b in zip(values,base63['priced_prefixes'][pid]))
    if expected_priced_prefixes is not None:
        assert digest(expected_priced_prefixes)==digest(allocated['priced_prefixes'])
    deltas63=[]
    for row,old in zip(allocated['rows'],base63['rows']):
        assert row['charge']<=old['charge']
        deltas63.append({'k':row['k'],'charge_reduction':old['charge']-row['charge'],
                        'integer_bound_gain':row['integer_lower_bound']-old['integer_lower_bound']})
    diagnostics={'owner_endpoints':admitted,'reduced_endpoints':reduced,'max_m':max_m,'max_n':max_n,
                 'sum_m_minus_n':reductions,'reduced_share':reduced/admitted if admitted else None}
    if expected_packing_diagnostics is not None:
        assert digest(expected_packing_diagnostics)==digest(diagnostics)
    result={'schema':'gamma.packing-entry-price.supplied.v1','base63':base63,'lambda_family':prices,
        'packing_diagnostics':diagnostics,'deltas_vs63':deltas63,
        'count_streams':count_streams,'price_caps':price_caps,'price_suffix_schedule':suffixes,**allocated,
        'production_forward_schedule_checked':expected_price_prefix_schedule is not None,
        'production_forward_schedule_sha256':digest(expected_price_prefix_schedule) if expected_price_prefix_schedule is not None else None,
        'work':{'baseline63_reconstructions':1,'additional_old_contexts':1,'old_occurrences_replayed':cursor,
            'old_bellman_edges_checked':bellman,'support_suffix_positions_checked':len(positions),'support_groups_classified':len(index.groups),
            'old_occurrences_reclassified':ac_replayed,'old_owned_occurrence_counts_checked':old_owned_checked,
            'banned_occurrences_matched':banned_occurrences,'z_input_symbols':z_symbols,'z_character_comparisons':z_comparisons,
            'z_histogram_cells':z_histogram_cells,'endpoints_inspected':endpoints,'banned_endpoints_skipped':banned_skips,
            'shared_allowed_endpoints_skipped':shared_skips,'one_owner_occurrences':admitted,'count_records':admitted,
            'q_evaluations':admitted,'packing_divisions':admitted,'pointwise_residual_checks':len(prices)*admitted,'price_residual_evaluations':len(prices)*admitted,
            'backward_candidates':backward_candidates,'production_forward_candidates':forward_candidates,
            'production_forward_positions_checked':forward_positions,
            'prefix_price_evaluations':sum(len(v) for v in base57['owner_prefixes'].values())*len(prices),
            'allocation_marginals_sorted':sum(len(v)-1 for v in allocated['priced_prefixes'].values())},
        'shared_dependency':'Unchanged63 independent baseline (including57) and33 Index/partition verifier; additional AC old q/d/support reconstruction.',
        'scalar_replay':'Numeric Z overlapping m; n=min(m,source length/entry length); backward prices; every supplied forward recurrence; full finite marginal sort.'}
    result['digests']={key+'_sha256':digest(result[key]) for key in (*COMMON_FIELDS,'price_suffix_schedule')}
    result['digests']['base63_sha256']=digest(scientific63(base63))
    return result


def z_counts(codes,start):
    """Exact within-source overlapping occurrence counts, transient O(n) state."""
    if not __debug__:raise RuntimeError('normal assertions required')
    assert type(codes) is list and codes and all(type(v) is int and v>=0 for v in codes)
    assert type(start) is int and 0<=start<len(codes)
    remaining=len(codes)-start;sequence=codes[start:]+[-1]+codes;z=[0]*len(sequence)
    left=right=comparisons=0
    for at in range(1,len(sequence)):
        if at<right:z[at]=min(right-at,z[at-left])
        while at+z[at]<len(sequence):
            comparisons+=1
            if sequence[z[at]]!=sequence[at+z[at]]:break
            z[at]+=1
        if at+z[at]>right:left,right=at,at+z[at]
    histogram=[0]*(remaining+1);offset=remaining+1
    for at in range(len(codes)):
        length=z[offset+at];assert 0<=length<=min(remaining,len(codes)-at)
        histogram[length]+=1
    counts=[0]*(remaining+1);total=0
    for length in range(remaining,0,-1):total+=histogram[length];counts[length]=total
    assert counts[remaining]>=1
    return counts,{'symbols':len(sequence),'comparisons':comparisons,'histogram_cells':len(histogram)}


def allocate(base,prices,caps,B,D):
    """Independent finite prefix construction and stable residual-marginal sort."""
    if not __debug__:raise RuntimeError('normal assertions required')
    assert type(B) is int and B>=0 and type(D) is int and D>0
    assert type(prices) is list and all(type(v) is int for v in prices) and prices==[0]+[D*2**r for r in range(14)]
    assert caps.keys()==base['owner_prefixes'].keys()
    assert all(type(v) is int and v>=0 for values in caps.values() for v in values)
    affine={};priced={};marginals=[]
    for pid,A in sorted(base['owner_prefixes'].items()):
        assert len(caps[pid])==len(prices)
        lines=[min(price*t+cap for price,cap in zip(prices,caps[pid])) for t in range(len(A))]
        values=[min(a,line) for a,line in zip(A,lines)]
        assert values[0]==0 and all(type(v) is int and v>=0 for v in values)
        increments=[b-a for a,b in zip(values,values[1:])]
        assert all(v>=0 for v in increments) and increments==sorted(increments,reverse=True)
        assert all(a<=b for a,b in zip(values,base['capped_prefixes'][pid]))
        affine[pid]=lines;priced[pid]=values
        marginals.extend((v,pid,rank) for rank,v in enumerate(increments,1))
    selected=sorted(marginals,key=lambda v:(-v[0],v[1],v[2]))[:B]
    one=[0];choices=[]
    for value,pid,rank in selected:one.append(one[-1]+value);choices.append([pid,rank,value])
    shared=base['shared_prefix'];rows=[];deltas=[];L=sum(base['base']['tightened']['path_numerators'].values())
    for k,old in enumerate(base['rows']):
        feasible=[(one[j]+shared[min(B-j,len(shared)-1)],j) for j in range(min(k,len(one)-1)+1)]
        charge,j=max(feasible,key=lambda item:(item[0],-item[1]));num=L-charge;lower,remainder=divmod(num,D)
        row={'k':k,'charge':charge,'one_owner_slots':j,'shared_slots':min(B-j,len(shared)-1),'numerator':num,
             'integer_lower_bound':lower+int(remainder!=0)}
        assert charge<=old['charge']
        rows.append(row);deltas.append({'k':k,'charge_reduction':old['charge']-charge,'integer_bound_gain':row['integer_lower_bound']-old['integer_lower_bound']})
    return {'affine_envelopes':affine,'priced_prefixes':priced,'one_owner_prefix':one,'marginal_choices':choices,
            'shared_prefix':shared,'rows':rows,'deltas_vs57':deltas}
