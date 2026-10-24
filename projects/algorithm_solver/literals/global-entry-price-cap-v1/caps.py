"""Supplied fixed global entry prices; all arcs, no loader or optimization.

Shares immutable63 DepthMap and JSON helpers. Reconstructs unchanged57 and a
separate53 potential/index context; neither baseline nor extra context is free.
"""
import hashlib
import importlib.util
from pathlib import Path

_spec=importlib.util.spec_from_file_location('global66_structure63',Path(__file__).resolve().parents[1]/'entry-price-path-cap-v1/caps.py')
structure63=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(structure63)
prior=structure63.prior
parent=structure63.parent
normalized=structure63.normalized
digest=structure63.digest
scientific57=structure63.scientific57
COMMON=('lambda_family','shared_counts','count_streams','price_caps','unpriced_caps','price_rows',
        'selected_price_index','global_charge','rows','deltas_vs57')


def check(texts,banned,old_pool,old_q,seed,alphabet,D,*,expected_source_hashes,
          expected_old_banned,expected_old_certificate=None,
          expected_occurrence_sha256=None,capacity=256):
    if not __debug__:raise RuntimeError('normal assertions required')
    assert type(capacity) is int and capacity>=0
    same_bans=expected_old_banned is banned
    banned=set(banned);expected_old_banned=banned if same_bans else set(expected_old_banned)
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
    prices=[0]+[D*2**r for r in range(14)];K=len(prices)
    mapping=structure63.DepthMap(obj.index)
    shared_counts=sorted([[eid,obj.index.groups[gid]['hi']-obj.index.groups[gid]['lo']]
                         for (gid,length),eid in obj.old_entry_ids.items() if obj.support[gid]==2])
    assert len({eid for eid,_ in shared_counts})==len(shared_counts)
    assert len(shared_counts)==sum(g['multiplicity'] for gid,g in enumerate(obj.index.groups) if obj.support[gid]==2)
    work={'baseline57_reconstructions':1,'additional53_contexts':1,
        'shared_structural_utility63':1,'structural_groups':len(obj.index.groups),
        'terminal_positions_checked':len(obj.positions),'shared_catalogue_entries':len(shared_counts),
        'ancestor_group_visits':0,'candidate_depths':0,'allowed_endpoints':0,'banned_endpoints':0,
        'owner_endpoints':0,'shared_endpoints':0,'multiplicity_cache_entries':0,'multiplicity_divisions':0,
        'q_evaluations':0,'price_residual_evaluations':0,'forward_arc_candidates':0,'forward_skip_candidates':0,
        'unpriced_arc_candidates':0,'unpriced_skip_candidates':0,'count_stream_records':0}
    quotients={};schedules={};unpriced_schedules={};caps={};unpriced_caps={};streams={}
    for pid,text in sorted(texts.items()):
        vectors=[[0]*(len(text)+1) for _ in prices];unpriced=[0]*(len(text)+1);d=obj.d[pid];source_stream=[]
        for start in range(len(text)):
            for values in vectors:
                values[start+1]=max(values[start+1],values[start]);work['forward_skip_candidates']+=1
            unpriced[start+1]=max(unpriced[start+1],unpriced[start]);work['unpriced_skip_candidates']+=1
            h=hashlib.sha256();arcs=0
            for gid in mapping.chain(pid,start):
                work['ancestor_group_visits']+=1;g=obj.index.groups[gid]
                support=obj.support[gid];assert support in (1,2)
                if support==1:assert obj.positions[g['lo']][0]==pid
                m=g['hi']-g['lo'];assert m>0
                excluded=set(g['excluded_lengths'])
                for length in range(g['first'],g['last']+1):
                    end=start+length;work['candidate_depths']+=1
                    assert (length in excluded)==(end in obj.index.banned_ends[pid][start])
                    if length in excluded:
                        work['banned_endpoints']+=1;continue
                    if m not in quotients:
                        quotients[m]=[price//m for price in prices]
                        work['multiplicity_cache_entries']+=1;work['multiplicity_divisions']+=K
                    h.update(f'[{end},{m}]\n'.encode('ascii'));arcs+=1
                    work['owner_endpoints' if support==1 else 'shared_endpoints']+=1
                    q=max(0,d[start]-d[end]-(9 if length==1 else -1)*D);work['q_evaluations']+=1
                    unpriced[end]=max(unpriced[end],unpriced[start]+q);work['unpriced_arc_candidates']+=1
                    for values,removed in zip(vectors,quotients[m]):
                        residual=max(q-removed,0)
                        values[end]=max(values[end],values[start]+residual)
                        work['price_residual_evaluations']+=1;work['forward_arc_candidates']+=1
            source_stream.append({'arcs':arcs,'sha256':h.hexdigest()})
            work['allowed_endpoints']+=arcs;work['count_stream_records']+=arcs
        assert vectors[0]==unpriced
        for values in vectors+[unpriced]:
            assert values[0]==0 and all(type(value) is int and value>=0 for value in values)
            assert all(a<=b for a,b in zip(values,values[1:]))
        schedules[pid]=vectors;unpriced_schedules[pid]=unpriced
        caps[pid]=[values[-1] for values in vectors];unpriced_caps[pid]=unpriced[-1];streams[pid]=source_stream
        assert caps[pid]==sorted(caps[pid],reverse=True)
    expected=sum(g['multiplicity']*(g['hi']-g['lo']) for g in obj.index.groups)
    expected_owner=sum(g['multiplicity']*(g['hi']-g['lo']) for gid,g in enumerate(obj.index.groups) if obj.support[gid]==1)
    raw_endpoints=sum(len(text)*(len(text)+1)//2 for text in texts.values())
    assert work['allowed_endpoints']==expected==work['owner_endpoints']+work['shared_endpoints']
    assert work['owner_endpoints']==expected_owner==base['work']['schedule_one_owner_occurrences']
    assert work['shared_endpoints']==sum(count for _,count in shared_counts)
    assert work['candidate_depths']==raw_endpoints==expected+work['banned_endpoints']
    assert work['banned_endpoints']==sum(len(ends) for rows in obj.index.banned_ends.values() for ends in rows)
    assert work['ancestor_group_visits']<=raw_endpoints
    assert work['price_residual_evaluations']==work['forward_arc_candidates']==K*expected
    L=sum(obj.path_numerators.values());price_rows=[]
    for i,price in enumerate(prices):
        residual=sum(values[i] for values in caps.values());entry_charge=price*capacity
        charge=entry_charge+residual;num=L-charge
        price_rows.append({'lambda':price,'entry_charge':entry_charge,'residual_cap':residual,'charge':charge,
                           'numerator':num,'integer_lower_bound':-(-num//D)})
    winner=min(range(K),key=lambda i:(price_rows[i]['charge'],prices[i]));global_charge=price_rows[winner]['charge']
    rows=[];deltas=[]
    for old in base['rows']:
        charge=min(old['charge'],global_charge);num=L-charge;lower=-(-num//D)
        rows.append({'k':old['k'],'charge':charge,'baseline57_charge':old['charge'],'global_charge':global_charge,
                     'numerator':num,'integer_lower_bound':lower,'charge_reduction_vs57':old['charge']-charge})
        deltas.append({'k':old['k'],'charge_reduction':old['charge']-charge,
                       'integer_bound_gain':lower-old['integer_lower_bound']})
    assert len(rows)==capacity+1
    result={'schema':'gamma.global-entry-price-cap.supplied.v1','base57':base,
        'lambda_family':prices,'shared_counts':shared_counts,'count_streams':streams,'price_caps':caps,
        'unpriced_caps':unpriced_caps,'price_prefix_schedule':schedules,'unpriced_prefix_schedule':unpriced_schedules,
        'price_rows':price_rows,'selected_price_index':winner,'global_charge':global_charge,'rows':rows,'deltas_vs57':deltas}
    result['digests']={key+'_sha256':digest(result[key]) for key in COMMON+('price_prefix_schedule','unpriced_prefix_schedule')}
    result['digests']['base57_sha256']=digest(scientific57(base));result['work']=work
    return result
