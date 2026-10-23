"""mip-audit-v1: exact MILP optima on random dev-fit sub-instances vs the frozen local search (FREEZE.md).

  audit.py --work DIR --output DIR/mip-audit/run-v1 [--parallel 6]

For each frozen (programs, seed): draw that many dev-fit IDs (random.Random(seed).sample), build the subset's pool
(substrings of 2-32 characters shared by at least two subset programs, never a complete source or solve body),
and solve min total selections with at most B=32 learned entries plus the 96 characters exactly with HiGHS
(scipy.optimize.milp). Path flows are a network flow once x is fixed, so only x is integral. Separately run the
minify-control-v1 local search (fallback alphabet, greedy refill, matched80-v3 exact local search, chosen-span
proposer, 60,000 trials) on the same subset at 128 entries. Validation sources are never opened.
"""
from pathlib import Path
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import coo_matrix
LIT=Path(__file__).resolve().parent.parent; sys.path[:0]=[str(LIT/'lagrange-select-v2'),str(LIT/'cost-decomposition-v1'),str(LIT),str(LIT/'pass2/working')]
import analyze, selection as sel
W=Path(os.environ.get('GAMMA_WORK','/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1'))
parent=json.loads((LIT/'cost-decomposition-v1/contract.json').read_text()); fit_ids=parent['partition']['dev_fit']


def instance(n, B, seed, lmax, secs):
    os.environ['PYTHONHASHSEED'] = '0'
    ids=random.Random(seed).sample(fit_ids,n)
    texts=analyze.load_sources(W,{**parent,'sources':[r for r in parent['sources'] if r['id'] in set(ids)]})
    pool=sel.build_pool(texts,sel.forbidden_strings(texts),lmax); E=len(pool); idx={s:k for k,s in enumerate(pool)}
    # nodes: per program positions 0..len; arcs: char arcs + pool arcs
    tail,head,ent=[],[],[]; base=0; src=[]; snk=[]
    for p,t in texts.items():
        m=len(t); src.append(base); snk.append(base+m)
        for i in range(m):
            tail.append(base+i); head.append(base+i+1); ent.append(-1)
            for l in range(2,min(lmax,m-i)+1):
                k=idx.get(t[i:i+l])
                if k is not None: tail.append(base+i); head.append(base+i+l); ent.append(k)
        base+=m+1
    na=len(tail); nv=E+na; tail=np.array(tail); head=np.array(head); ent=np.array(ent)
    cost=np.zeros(nv); cost[E:]=1
    arcs=np.arange(na)
    eq=coo_matrix((np.concatenate([np.ones(na),-np.ones(na)]),(np.concatenate([tail,head]),np.concatenate([E+arcs,E+arcs]))),shape=(base,nv)).tocsr()
    rhs=np.zeros(base); rhs[src]=1; rhs[snk]=-1
    f=np.flatnonzero(ent>=0)
    link=coo_matrix((np.concatenate([np.ones(len(f)),-np.ones(len(f))]),(np.concatenate([np.arange(len(f))]*2),np.concatenate([E+f,ent[f]]))),shape=(len(f),nv)).tocsr()
    bud=np.zeros(nv); bud[:E]=1
    integ=np.zeros(nv); integ[:E]=1
    t0=time.time()
    res=milp(cost,constraints=[LinearConstraint(eq,rhs,rhs),LinearConstraint(link,-np.inf,0),LinearConstraint(bud[None,:],-np.inf,B)],integrality=integ,bounds=Bounds(0,1),options={'time_limit':secs,'disp':False})
    milp_s=time.time()-t0
    chosen=[pool[k] for k in range(E) if res.x is not None and res.x[k]>0.5]
    exact=sel.exact_fit(texts,sel.ALPHABET+chosen) if res.x is not None else None
    # local search: same procedure as the frozen pipeline, at width with 96+B entries; fit start from alphabet (minify-control style)
    m2=sel.module('ls_m2',LIT/'style150-v2/measure.py'); v3=m2.v3
    sources={pid:{'style':t} for pid,t in texts.items()}
    mc=json.loads((LIT/'minify-control-v1/contract.json').read_text())['search']
    width=(96+B-1).bit_length()
    assert 2**width==96+B, 'B must make a power of two'
    budget=v3.Budget({'trials':60000,'seconds':1800}); nb={**mc['neighborhood'],'refill_shortlist':24}
    st=v3.evaluate(sources,list(sel.ALPHABET),width,None,budget); prop=m2.hybrid_chosen([],sources)
    st,_=v3.refill(sources,st,width,prop,nb,24,budget); st,stop=v3.local_search(sources,st,width,prop,mc['neighborhood'],budget,[])
    return ({'n':n,'seed':seed,'B':B,'lmax':lmax,'pool':E,'arcs':na,'milp_status':int(res.status),'milp_obj':res.fun,'mip_gap':getattr(res,'mip_gap',None),
     'milp_dual_bound':getattr(res,'mip_dual_bound',None),'milp_seconds':round(milp_s,1),'milp_exact_fit':exact,'local_search_fit':st['selections'],'ls_trials':budget.trials,'ls_stop':stop,'ls_seconds':budget.elapsed(),
     'ids':sorted(ids),'milp_dictionary_sha256':hashlib.sha256(json.dumps(sorted(chosen)).encode()).hexdigest(),
     'ls_dictionary_sha256':hashlib.sha256(json.dumps(sorted(st['vocab'])).encode()).hexdigest()})


def job(args):
    return instance(*args)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--parallel', type=int, default=6); a = ap.parse_args()
    c = json.loads((Path(__file__).resolve().parent / 'contract.json').read_text())
    for rel, h in c['code_hashes'].items(): assert hashlib.sha256((LIT / rel).read_bytes()).hexdigest() == h, rel
    os.environ['GAMMA_WORK'] = str(a.work.resolve())  # read by spawned workers at import
    a.output.mkdir(parents=True, exist_ok=False)
    jobs = [(n, c['B'], s, c['max_length'], c['milp_seconds']) for n in c['sizes'] for s in c['seeds'][str(n)]]
    started = time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(a.parallel, mp_context=multiprocessing.get_context('spawn')) as ex:
        rows = list(ex.map(job, jobs))
    (a.output / 'results.json').write_text(json.dumps({'contract_sha256': hashlib.sha256((Path(__file__).resolve().parent / 'contract.json').read_bytes()).hexdigest(),
                                                      'seconds': time.monotonic() - started, 'rows': rows}, indent=1) + '\n')
    for r in rows:
        print(json.dumps({k: r[k] for k in ('n', 'seed', 'milp_status', 'milp_obj', 'milp_dual_bound', 'milp_exact_fit', 'local_search_fit', 'milp_seconds')}), flush=True)


if __name__ == '__main__':
    main()
