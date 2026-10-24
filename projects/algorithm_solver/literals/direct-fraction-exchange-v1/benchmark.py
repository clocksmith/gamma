"""One bounded invented-data complexity measurement; no private-input API."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import random
import resource
import signal
import sys
import time
import mechanism as m

HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def fixture():
    rng=random.Random(4401);alphabet='abcdefghijklmnop'
    lengths=[100+(137*i)%301 for i in range(300)];lengths[-1]+=75000-sum(lengths)
    texts={str(p):''.join(rng.choice(alphabet) for _ in range(n)) for p,n in enumerate(lengths)}
    counts=Counter(t[i:i+k] for t in texts.values() for k in range(2,9) for i in range(len(t)-k+1))
    ranked=sorted(counts,key=lambda w:(-counts[w],len(w),w))
    pool=sorted(set(alphabet)|set(ranked[:2048-len(alphabet)]))
    seed=sorted(set(alphabet)|set(ranked[:249-len(alphabet)]))
    assert len(pool)==2048 and len(seed)==249
    return texts,pool,seed


def specification():
    texts,pool,seed=fixture()
    return {'synthetic_only':True,'programs':300,'characters':75000,'pool_entries':2048,'seed_entries':249,
            'sources_sha256':digest(texts),'pool_sha256':digest(pool),'seed_sha256':digest(seed),
            'core':6,'address_space_bytes':8*1024**3,'worker_seconds':55,'outer_seconds':60,'swap_addition_shortlist':4,
            'code_hashes':{p.name:sha(p) for p in (HERE/'mechanism.py',HERE/'test_mechanism.py',HERE/'benchmark.py')},
            'parent_contract_sha256':sha(HERE.parent/'fraction-primal-repair-v1/contract.json'),
            'python_bin':str(Path(sys.executable).resolve()),'python_sha256':sha(Path(sys.executable).resolve())}


def main():
    m.require_checks()
    if sys.argv[1:]==['--make-spec']:
        (HERE/'synthetic-spec.json').write_text(json.dumps(specification(),sort_keys=True,indent=2)+'\n');return
    assert not sys.argv[1:]
    spec=json.loads((HERE/'synthetic-spec.json').read_text());assert spec==specification()
    os.sched_setaffinity(0,{spec['core']});resource.setrlimit(resource.RLIMIT_AS,(spec['address_space_bytes'],)*2)
    started=time.monotonic();phase='fixture';result={'synthetic_only':True,'complete':False,'spec_sha256':sha(HERE/'synthetic-spec.json'),'stages':{}}
    def save():
        result['elapsed']=time.monotonic()-started;result['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        (HERE/'synthetic-results.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    def alarm(*_):raise TimeoutError('synthetic cap')
    signal.signal(signal.SIGALRM,alarm);signal.alarm(spec['worker_seconds'])
    try:
        texts,pool,seed=fixture();phase='graph';clock=time.monotonic()
        graph=m.Graph(texts,pool);current=graph.initial(seed)
        result['stages']['graph_seconds']=time.monotonic()-clock
        result.update(arcs=graph.arcs,transitions=graph.transitions,initial_objective=list(current['objective']))
        phase='all_additions';clock=time.monotonic();scores=[];best=None;affected=0
        for word in pool:
            if word in current['active']:continue
            trial,receipt=graph.evaluate(current,add=[word]);assert trial is not None
            scores.append((trial['objective'],word));affected+=receipt['affected_programs']
            if best is None or (trial['objective'],trial['order'])<(best['objective'],best['order']):best=trial
        result['stages']['all_additions_seconds']=time.monotonic()-clock
        result.update(addition_evaluations=len(scores),addition_program_recomputations=affected,best_addition_objective=list(best['objective']))
        save()
        phase='all_removals';clock=time.monotonic();failures=0;affected=0
        for word in sorted(current['active']):
            trial,receipt=graph.evaluate(current,remove=[word]);failures+=trial is None;affected+=receipt['affected_programs']
        result['stages']['all_removals_seconds']=time.monotonic()-clock
        result.update(removal_evaluations=len(current['active']),removal_coverage_failures=failures,removal_program_recomputations=affected)
        save()
        phase='swap_sweep';clock=time.monotonic();evaluated=0;failures=0;affected=0;best=None
        shortlist=[word for objective,word in sorted(scores)[:spec['swap_addition_shortlist']]]
        for add in shortlist:
            for remove in sorted(current['active']):
                trial,receipt=graph.evaluate(current,add=[add],remove=[remove]);evaluated+=1;affected+=receipt['affected_programs']
                if trial is None:failures+=1;continue
                if best is None or (trial['objective'],trial['order'])<(best['objective'],best['order']):best=trial
        result['stages']['swap_sweep_seconds']=time.monotonic()-clock
        result.update(swap_evaluations=evaluated,swap_coverage_failures=failures,swap_program_recomputations=affected,
                      best_swap_objective=list(best['objective']) if best else None,complete=True)
    except BaseException as error:
        result.update(failure_type=type(error).__name__,failed_phase=phase);raise
    finally:signal.alarm(0);save();print(json.dumps(result),flush=True)


if __name__=='__main__':main()
