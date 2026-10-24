"""Fixed finite integer ascent; measured prototype files remain unchanged."""
import math
import time
import common as c


def step(denominator,iteration):
    assert type(denominator) is int and denominator>0 and type(iteration) is int and iteration>=0
    root=math.isqrt(iteration+1);root+=root*root<iteration+1
    return max(1,denominator//(4*root))


def proof(result):
    return {key:result[key] for key in ('numerator','denominator','joint_path_numerator','top_capacity_numerator','selected_a','assignments')}


def search(index,contract,baseline,save):
    D=contract['denominator'];q=c.p.zeros(index.texts);rows=[];best=None;stop='point_limit'
    for ordinal in range(contract['search']['points']):
        clock=time.monotonic()
        got=c.p.oracle(index,q,256,D,endpoint_bytes=contract['limits']['endpoint_bytes'])
        assert got['joint_family_feasible'],'Parent42 baseline family must remain feasible independently of q'
        if ordinal==0:
            assert got['numerator']==baseline
            save('zero',q,proof(got))
        improved=best is None or got['numerator']>best['numerator']
        if improved:
            save('best',q,proof(got));best={'numerator':got['numerator'],'iteration':ordinal,'q_digest':c.digest(q)}
        norm=c.p.dot(got['gradient'],got['gradient']);s=step(D,ordinal)
        moved=None
        if ordinal+1<contract['search']['points'] and norm:
            next_q=c.p.update(q,got['gradient'],s);moved=next_q!=q
        rows.append({'iteration':ordinal,'q_digest':c.digest(q),'numerator_search_only':got['numerator'],
                     'selected_a_search_only':got['selected_a'],'gradient_squared_norm':norm,'step':s,
                     'projected_movement':moved,'retained_best':improved,'endpoint_peak_bytes':got['endpoint_peak_bytes'],
                     'phase_seconds':got['phase_seconds'],'seconds':time.monotonic()-clock})
        save('progress',None,{'complete':False,'trajectory_search_diagnostics':rows,'best':best})
        if norm==0:stop='zero_supergradient';break
        if moved is False:stop='unchanged_projection';break
        if ordinal+1<contract['search']['points']:q=next_q
    assert best['numerator']>=baseline
    return {'trajectory_search_diagnostics':rows,'best':best,'stop':stop}
