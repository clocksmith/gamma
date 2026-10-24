"""Item71 supplied owner-packing counts and fixed-price forward caps.

Full unchanged63 baseline plus separate53 context are charged explicitly.
Only finite owner allocation changes; shared charges and original q53 stay fixed.
No loader, optimizer, corpus fixture or execution launcher is present.
"""
import hashlib
import importlib.util
import json
import math
from pathlib import Path

_spec=importlib.util.spec_from_file_location('packing71_parent63',Path(__file__).resolve().parents[1]/'entry-price-path-cap-v1/caps.py')
prior=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(prior)
parent=prior.parent
COMMON=('lambda_family','count_streams','price_caps','affine_envelopes','priced_prefixes',
        'one_owner_prefix','marginal_choices','shared_prefix','rows','deltas_vs63','deltas_vs57','packing_diagnostics')


def normalized(value):
    """Normalize before sorting, rejecting ambiguous JSON key collisions."""
    if type(value) is dict:
        assert all(type(key) in (str,int) for key in value)
        out={str(key):normalized(v) for key,v in value.items()}
        assert len(out)==len(value)
        return out
    if type(value) in (tuple,list):return [normalized(v) for v in value]
    assert type(value) in (str,int,bool,float,type(None))
    if type(value) is float:assert math.isfinite(value)
    return value


def digest(value):
    return hashlib.sha256(json.dumps(normalized(value),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def scientific63(base):
    return {'schema':base['schema'],'base57':prior.scientific57(base['base57']),
            **{key:base[key] for key in prior.COMMON}}


def scientific(result):
    return {'schema':result['schema'],'base63':scientific63(result['base63']),
            **{key:result[key] for key in COMMON}}


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
    assert obj.path_numerators==base['base57']['base']['tightened']['path_numerators']
    assert obj.occurrence_sha256==base['base57']['base']['tightened']['occurrence_sha256']
    assert digest(obj.d)==base['base57']['base']['digests']['potentials_sha256']
    assert digest(obj.tight_weights)==base['base57']['base']['digests']['tightened_old_weights_sha256']
    prices=[0]+[D*(2**rank) for rank in range(14)];K=len(prices);assert K==15
    structure=prior.DepthMap(obj.index)
    quotients={};schedules={};price_caps={};streams={}
    work={'baseline63_reconstructions':1,'additional53_contexts':1,'structural_groups':len(obj.index.groups),
        'terminal_positions_checked':len(obj.positions),'ancestor_group_visits':0,'candidate_owner_depths':0,
        'allowed_owner_endpoints':0,'banned_owner_endpoints':0,'packing_cache_entries':0,
        'packing_quotient_divisions':0,'packing_divisions':0,'pointwise_residual_checks':0,'q_evaluations':0,'price_residual_evaluations':0,
        'forward_arc_candidates':0,'forward_skip_candidates':0,'count_stream_records':0,
        'prefix_price_evaluations':0,'forward_vector_positions_checked':0}
    diagnostics={'owner_endpoints':0,'reduced_endpoints':0,'max_m':0,'max_n':0,
                 'sum_m_minus_n':0,'reduced_share':None}
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
                    n=min(m,len(text)//length);work['packing_divisions']+=1
                    assert 1<=n<=m
                    diagnostics['owner_endpoints']+=1
                    diagnostics['reduced_endpoints']+=int(n<m)
                    diagnostics['max_m']=max(diagnostics['max_m'],m)
                    diagnostics['max_n']=max(diagnostics['max_n'],n)
                    diagnostics['sum_m_minus_n']+=m-n
                    if n not in quotients:
                        quotients[n]=[price//n for price in prices]
                        work['packing_cache_entries']+=1;work['packing_quotient_divisions']+=K
                    removed=quotients[n]
                    count_hash.update((f'[{end},{m},{n}]\n').encode('ascii'));arcs+=1
                    q=max(0,d[start]-d[end]-(9 if length==1 else -1)*D)
                    work['q_evaluations']+=1
                    for price,values,amount in zip(prices,vectors,removed):
                        residual=max(q-amount,0)
                        assert residual<=max(q-price//m,0)
                        work['pointwise_residual_checks']+=1
                        values[end]=max(values[end],values[start]+residual)
                        work['price_residual_evaluations']+=1;work['forward_arc_candidates']+=1
            work['allowed_owner_endpoints']+=arcs;work['count_stream_records']+=arcs
            source_stream.append({'arcs':arcs,'sha256':count_hash.hexdigest()})
        assert vectors[0]==base['price_prefix_schedule'][pid][0]==base['base57']['owner_prefix_schedule'][pid]
        for vector,old in zip(vectors,base['price_prefix_schedule'][pid]):
            assert len(vector)==len(old) and all(a<=b for a,b in zip(vector,old))
            work['forward_vector_positions_checked']+=len(vector)
        schedules[pid]=vectors;price_caps[pid]=[values[-1] for values in vectors];streams[pid]=source_stream
    expected=sum(g['multiplicity']*(g['hi']-g['lo']) for gid,g in enumerate(obj.index.groups) if obj.support[gid]==1)
    assert work['allowed_owner_endpoints']==expected==base['work']['allowed_owner_endpoints']==base['base57']['work']['schedule_one_owner_occurrences']
    assert work['ancestor_group_visits']<=sum(len(t)*(len(t)+1)//2 for t in texts.values())
    assert work['candidate_owner_depths']==work['allowed_owner_endpoints']+work['banned_owner_endpoints']
    assert work['price_residual_evaluations']==work['forward_arc_candidates']==K*expected
    assert diagnostics['owner_endpoints']==expected
    if expected:diagnostics['reduced_share']=diagnostics['reduced_endpoints']/expected
    envelopes={};prefixes={}
    for pid,values in base['base57']['owner_prefixes'].items():
        envelope=[min(price*t+cap for price,cap in zip(prices,price_caps[pid])) for t in range(len(values))]
        work['prefix_price_evaluations']+=K*len(values)
        prefix=[min(weight,line) for weight,line in zip(values,envelope)]
        increments=[b-a for a,b in zip(prefix,prefix[1:])]
        assert prefix[0]==0 and all(v>=0 for v in increments)
        assert all(a>=b for a,b in zip(increments,increments[1:]))
        assert all(a<=b for a,b in zip(prefix,base['priced_prefixes'][pid]))
        assert len(prefix)==min(capacity,base['base57']['owner_entry_counts'][pid])+1
        envelopes[pid]=envelope;prefixes[pid]=prefix
    one,choices,rows,offers,pops=prior.allocate(prefixes,base['shared_prefix'],sum(obj.path_numerators.values()),D,capacity)
    work.update(allocation_heap_offers=offers,allocation_heap_pops=pops)
    delta_sets=[]
    for old_rows in (base['rows'],base['base57']['rows']):
        deltas=[]
        for row,old in zip(rows,old_rows):
            assert row['charge']<=old['charge']
            deltas.append({'k':row['k'],'charge_reduction':old['charge']-row['charge'],
                'integer_bound_gain':row['integer_lower_bound']-old['integer_lower_bound']})
        delta_sets.append(deltas)
    result={'schema':'gamma.packing-entry-price.supplied.v1','base63':base,'lambda_family':prices,
        'count_streams':streams,'price_caps':price_caps,'price_prefix_schedule':schedules,
        'affine_envelopes':envelopes,'priced_prefixes':prefixes,'one_owner_prefix':one,
        'marginal_choices':choices,'shared_prefix':base['shared_prefix'],'rows':rows,
        'deltas_vs63':delta_sets[0],'deltas_vs57':delta_sets[1],'packing_diagnostics':diagnostics}
    result['digests']={key+'_sha256':digest(result[key]) for key in COMMON+('price_prefix_schedule',)}
    result['digests']['base63_sha256']=digest(scientific63(base))
    result['work']=work
    return result
