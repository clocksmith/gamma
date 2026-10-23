"""Verified parent lift, exact bin-release diagnostics, then projected ascent."""
import math
import time
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import implicit
from backend import dual

CERT_KEYS=('numerator','denominator','integer_lower_bound','path_numerators','top_capacity_numerator')

def release_sweep(initial):
    """Yield all22 fixed diagnostics; equality dedup uses exact coordinate tuples."""
    order=[(pid,i) for pid in sorted(initial) for i in range(len(initial[pid]))]
    seen={}
    for b in range(len(implicit.BINS)):
        original=tuple(initial[p][i][b] for p,i in order)
        for operation in ('half_floor','zero'):
            values=tuple(v//2 if operation=='half_floor' else 0 for v in original)
            record={'bin':b,'operation':operation}
            if values==original:
                yield {**record,'status':'duplicate_baseline'},None;continue
            key=(b,values)
            if key in seen:
                yield {**record,'status':'duplicate_diagnostic','duplicate_of':seen[key]},None;continue
            seen[key]=[b,operation]
            q={p:[row[:] for row in rows] for p,rows in initial.items()}
            for (p,i),v in zip(order,values):q[p][i][b]=v
            yield {**record,'status':'evaluate'},q


def optimize(index,seed,old_q,parent_certificate,capacity,cfg,trace,checkpoint=None):
    implicit.require_checks();started=time.monotonic();D=cfg['denominator']
    assert parent_certificate['denominator']==D
    old=index.base.certificate(old_q,capacity,D)
    assert implicit.parent.verify(index.base,old_q,capacity,D)==old['numerator']
    assert all(parent_certificate[k]==old[k] for k in CERT_KEYS)
    initial=implicit.lift_start_multipliers(old_q)
    initial_cert=index.certificate(initial,capacity,D)
    assert all(initial_cert[k]==old[k] for k in CERT_KEYS)
    assert implicit.verify(index,initial,capacity,D)==old['numerator']
    assert len(seed)==len(set(seed))<=capacity and all(seed) and not set(seed)&index.base.banned
    seed=[word for word in seed if implicit.parent.occurrence_interval(index.texts,index.base.positions,word)[0]<implicit.parent.occurrence_interval(index.texts,index.base.positions,word)[1]]
    upper=seed_cost=dual.objective(index.texts,seed);best_vocab=seed[:];generated_vocab=None;generated_cost=None
    assert initial_cert['numerator']<=upper*D
    best_q=initial;best_cert=initial_cert;theta=1.;stalls=0;attempts=infeasible=executed=0;stop='iteration_limit';diagnostics=[]
    def retain(q,cert):
        nonlocal best_q,best_cert
        if cert['numerator']>best_cert['numerator']:
            best_q,best_cert=q,cert
            if checkpoint:checkpoint(best_q,{k:best_cert[k] for k in CERT_KEYS})
            return True
        return False
    if checkpoint:checkpoint(best_q,{k:best_cert[k] for k in CERT_KEYS})
    trace({'event':'initial','exact_numerator':best_cert['numerator'],'best_numerator':best_cert['numerator'],
           'upper_bound':upper,'seconds':time.monotonic()-started})
    for record,q in release_sweep(initial):
        if q is not None:
            if time.monotonic()-started>=cfg['seconds']:record['status']='not_started_budget'
            else:
                cert=index.certificate(q,capacity,D);assert cert['numerator']<=upper*D
                record.update(status='evaluated',exact_numerator=cert['numerator'],improved=retain(q,cert))
        record.update(best_numerator=best_cert['numerator'],seconds=time.monotonic()-started)
        diagnostics.append(record);trace({'event':'release',**record})
    q=best_q
    for iteration in range(cfg['iterations']):
        if time.monotonic()-started>=cfg['seconds']:stop='time_limit';break
        cert=index.certificate(q,capacity,D);improved=retain(q,cert)
        stalls=0 if improved else stalls+1
        if stalls>=cfg['halve_after']:theta/=2;stalls=0
        if iteration%cfg['primal_every']==0:
            for longest in (False,True):
                vocab=index.selected_vocabulary(cert['selected_pieces'],longest_first=longest);attempts+=1
                try:value=dual.objective(index.texts,vocab)
                except ValueError:infeasible+=1;continue
                if generated_cost is None or value<generated_cost:generated_cost,generated_vocab=value,vocab
                if value<upper:upper,best_vocab=value,vocab
        assert cert['numerator']<=upper*D
        selected=index.selected_occurrences(cert['selected_pieces'])
        gradients={p:np.asarray(cert['path_starts'][p],dtype=np.int64)-np.asarray(selected[p],dtype=np.int64) for p in q}
        assert sum(len(rows) for rows in q.values())*len(implicit.BINS)*max(1,capacity)**2<2**63
        norm=sum(int(np.sum(g*g,dtype=np.int64)) for g in gradients.values())
        trace({'event':'ascent','iteration':iteration,'exact_numerator':cert['numerator'],'best_numerator':best_cert['numerator'],
               'integer_lower_bound':cert['integer_lower_bound'],'upper_bound':upper,'generated_objective':generated_cost,
               'theta':theta,'gradient_norm_squared':norm,'seconds':time.monotonic()-started})
        executed+=1
        if best_cert['integer_lower_bound']==upper:stop='exact_primal_optimum_certificate';break
        if norm==0:stop='restricted_dual_stationary';break
        step=theta*((upper*D-cert['numerator'])/D)/norm
        updated={p:np.maximum(0.,np.asarray(q[p],dtype=float)/D+step*gradients[p]) for p in q}
        assert all(np.all(np.isfinite(a)) and np.all(a>=0) for a in updated.values())
        q={p:[[math.floor(float(value)*D) for value in row] for row in a] for p,a in updated.items()}
    assert best_cert['numerator']>=initial_cert['numerator']
    assert implicit.verify(index,best_q,capacity,D)==best_cert['numerator']
    summary={k:best_cert[k] for k in CERT_KEYS}
    summary.update(independent_partition_and_integer_replay=True,excludes_ten_percent=summary['integer_lower_bound']>0)
    info={'certificate':summary,'initial_certificate':{k:initial_cert[k] for k in CERT_KEYS},
          'initial_q_all_zero':all(v==0 for rows in old_q.values() for v in rows),'bin_release':diagnostics,
          'seed_objective':seed_cost,'best_objective':upper,'generated_objective':generated_cost,
          'iterations':executed,'stop':stop,'primal_attempts':attempts,'primal_infeasible':infeasible,
          'finite_numerator_gain':best_cert['numerator']-initial_cert['numerator'],
          'seconds':time.monotonic()-started}
    return info,best_q,seed,best_vocab,generated_vocab
