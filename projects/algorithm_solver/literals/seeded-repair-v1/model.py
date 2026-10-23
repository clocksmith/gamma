"""Identical HiGHS repair models with an optional fully checked feasible MIP start."""
import importlib.util
from pathlib import Path
import time
import numpy as np
from scipy.sparse import coo_matrix,vstack
from scipy.optimize._highspy import _core as h
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
spec=importlib.util.spec_from_file_location('seeded_slot_repair',LIT/'character-slots-v1/repair.py');slot=importlib.util.module_from_spec(spec);spec.loader.exec_module(slot)
analyze=slot.analyze


def build(texts,fixed,candidates,capacity,incumbent):
    started=time.monotonic();fixed=set(fixed);candidates=list(candidates);C=len(candidates);index={s:i for i,s in enumerate(candidates)}
    assert len(index)==C and not fixed&set(candidates) and all(fixed|set(candidates))
    assert set(incumbent)<=fixed|set(candidates) and len(set(incumbent)-fixed)<=capacity
    maxlen=max(map(len,fixed|set(candidates)),default=1);tails=[];heads=[];entries=[];sources=[];sinks=[];base=0;used=[];initial=0
    for pid,text in sorted(texts.items()):
        seq=analyze.shortest_encode(text,incumbent);initial+=len(seq);start_positions={};offset=0
        for idx in seq:
            word=incumbent[idx];start_positions[offset]=word;offset+=len(word)
        assert offset==len(text)
        sources.append(base);sinks.append(base+len(text))
        for i in range(len(text)):
            for length in range(1,min(maxlen,len(text)-i)+1):
                word=text[i:i+length]
                if word in fixed or word in index:
                    tails.append(base+i);heads.append(base+i+length);entries.append(-1 if word in fixed else index[word])
                    if start_positions.get(i)==word:used.append(len(entries)-1)
        base+=len(text)+1
    tails=np.asarray(tails,dtype=np.int64);heads=np.asarray(heads,dtype=np.int64);entries=np.asarray(entries,dtype=np.int64)
    A=len(entries);V=C+A;arcs=np.arange(A);cost=np.zeros(V);cost[C:]=1
    flow=coo_matrix((np.concatenate([np.ones(A),-np.ones(A)]),(np.concatenate([tails,heads]),np.concatenate([C+arcs,C+arcs]))),shape=(base,V)).tocsr()
    rhs=np.zeros(base);rhs[sources]=1;rhs[sinks]=-1
    optional=np.flatnonzero(entries>=0);J=len(optional)
    links=coo_matrix((np.concatenate([np.ones(J),-np.ones(J)]),(np.concatenate([np.arange(J),np.arange(J)]),np.concatenate([C+optional,entries[optional]]))),shape=(J,V)).tocsr()
    budget=coo_matrix((np.ones(C),(np.zeros(C,dtype=int),np.arange(C))),shape=(1,V)).tocsr()
    matrix=vstack([flow,links,budget],format='csc');lower=np.concatenate([rhs,np.full(J+1,-np.inf)]);upper=np.concatenate([rhs,np.zeros(J),[capacity]])
    start=np.zeros(V)
    for word in set(incumbent)-fixed:start[index[word]]=1
    start[C+np.asarray(used,dtype=int)]=1
    values=matrix@start
    assert np.all(start>=0) and np.all(start<=1) and np.all(start[:C]==np.floor(start[:C]))
    assert np.all(values>=lower) and np.all(values<=upper) and int(cost@start)==initial
    assert max(matrix.shape)<2**31 and matrix.nnz<2**31
    return {'matrix':matrix,'lower':lower,'upper':upper,'cost':cost,'start':start,'candidate_count':C,'initial':initial,
            'arcs':A,'variables':V,'build_seconds':time.monotonic()-started,'start_nonzero':int(np.count_nonzero(start))}


def solve(model,candidates,warm,seconds,seed=260):
    started=time.monotonic();m=model;matrix=m['matrix'];lp=h.HighsLp();V=m['variables'];R=len(m['upper'])
    lp.num_col_=V;lp.num_row_=R;lp.col_cost_=m['cost'];lp.col_lower_=np.zeros(V);lp.col_upper_=np.ones(V);lp.row_lower_=m['lower'];lp.row_upper_=m['upper']
    lp.a_matrix_.num_col_=V;lp.a_matrix_.num_row_=R;lp.a_matrix_.format_=h.MatrixFormat.kColwise
    lp.a_matrix_.start_=matrix.indptr.astype(np.int32);lp.a_matrix_.index_=matrix.indices.astype(np.int32);lp.a_matrix_.value_=matrix.data
    lp.integrality_=[h.HighsVarType.kInteger]*m['candidate_count']+[h.HighsVarType.kContinuous]*(V-m['candidate_count'])
    solver=h._Highs()
    for key,value in {'output_flag':False,'time_limit':float(seconds),'mip_rel_gap':0.,'threads':1,'random_seed':seed}.items():assert solver.setOptionValue(key,value)==h.HighsStatus.kOk,key
    assert solver.passModel(lp)==h.HighsStatus.kOk
    supplied=None
    if warm:
        point=h.HighsSolution();point.col_value=m['start'];point.row_value=matrix@m['start'];point.value_valid=True
        status=solver.setSolution(point);assert status==h.HighsStatus.kOk;supplied=int(status)
    status=solver.run();assert status!=h.HighsStatus.kError
    info=solver.getInfo();solution=solver.getSolution();model_status=solver.getModelStatus()
    feasible=bool(solution.value_valid and info.primal_solution_status==h.kSolutionStatusFeasible)
    chosen=[];fun=None;residual=None
    if feasible:
        x=np.asarray(solution.col_value);values=matrix@x;eps=1e-6
        assert np.all(x>=-eps) and np.all(x<=1+eps) and np.all(values>=m['lower']-eps) and np.all(values<=m['upper']+eps)
        assert np.max(np.abs(x[:m['candidate_count']]-np.rint(x[:m['candidate_count']])),initial=0)<=eps
        fun=float(m['cost']@x);assert abs(fun-info.objective_function_value)<=eps
        chosen=[s for i,s in enumerate(candidates) if x[i]>.5]
        residual=float(info.max_primal_infeasibility)
    # A supplied valid incumbent must survive a limited solve. Do not hide a solver failure with a fallback.
    if warm:assert feasible and fun<=m['initial']+1e-6
    def finite(x):return float(x) if np.isfinite(x) else None
    return chosen,{'warm':warm,'set_solution_status':supplied,'model_status':int(model_status),'message':solver.modelStatusToString(model_status),
        'optimal':model_status==h.HighsModelStatus.kOptimal,'feasible':feasible,'objective':fun,'dual_bound':finite(info.mip_dual_bound),
        'gap':finite(info.mip_gap),'nodes':int(info.mip_node_count),'max_primal_infeasibility':residual,
        'solver_run_seconds':solver.getRunTime(),'call_seconds':time.monotonic()-started}
