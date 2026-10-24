"""One bounded invented full-sweep measurement; never loads private inputs."""
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
import prototype as m

HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

class Deadline(BaseException):pass


def fixture():
    # Same disclosed invented fixture as44, without reading its private inputs.
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
    texts,pool,seed=fixture();contract_path=HERE.parent/'direct-fraction-exchange-v1/contract.json'
    c=json.loads(contract_path.read_text())
    for rel,d in c['code_hashes'].items():assert sha(HERE.parent/rel)==d,rel
    for path,d in c['runtime_files'].items():assert sha(path)==d,path
    return {'synthetic_only':True,'programs':300,'characters':sum(map(len,texts.values())),
            'max_source_length':max(map(len,texts.values())),'pool_entries':len(pool),'seed_entries':len(seed),
            'sources_sha256':digest(texts),'pool_sha256':digest(pool),'seed_sha256':digest(seed),
            'core':4,'address_space_bytes':8*1024**3,'worker_seconds':55,'outer_seconds':60,'shortlist':4,
            'max_arcs':1000000,'max_transitions':20000000,'decoder_bytes':13010,
            'code_hashes':{name:sha(HERE/name) for name in ('prototype.py','test_prototype.py','synthetic.py')},
            'parent44_contract_sha256':sha(contract_path),'parent44_code_pins':len(c['code_hashes']),
            'python_bin':str(Path(sys.executable).resolve()),'python_sha256':sha(Path(sys.executable).resolve()),
            'python_version':sys.version}


def main():
    if sys.argv[1:]==['--make-spec']:
        (HERE/'synthetic-spec.json').write_text(json.dumps(specification(),sort_keys=True,indent=2)+'\n');return
    assert not sys.argv[1:]
    started=time.monotonic();phase='preflight';out={'synthetic_only':True,'complete':False}
    def expired(*_):raise Deadline('55-second whole invented measurement')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,55)
    try:
        os.sched_setaffinity(0,{4});resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,)*2)
        spec=json.loads((HERE/'synthetic-spec.json').read_text());assert spec==specification()
        out['spec_sha256']=sha(HERE/'synthetic-spec.json');phase='fixture';texts,pool,seed=fixture()
        phase='graph';clock=time.monotonic();g=m.Graph(texts,pool,seed,banned=texts.values(),decoder_bytes=spec['decoder_bytes'],max_arcs=spec['max_arcs'],max_transitions=spec['max_transitions'])
        out.update(graph_seconds=time.monotonic()-clock,arcs=g.arcs,transitions=g.transitions,
                   seed_N=g.seed['N'],seed_C=g.seed['C'],seed_full_package=g.seed['full_package_bytes'])
        phase='full_sweep';clock=time.monotonic();best,receipt=m.sweep(g,g.seed,spec['shortlist'])
        out.update(sweep_seconds=time.monotonic()-clock,counters=receipt['counters'],opportunity_count=len(receipt['opportunities']),
                   opportunity_sha256=digest(receipt['opportunities']),shortlist_pool_ids=receipt['shortlist_ids'],
                   strict_improvement=receipt['strict_improvement'],best_N=best['N'],best_C=best['C'],
                   best_full_package=best['full_package_bytes'],best_cap_failures=len(best['cap_failures']),
                   canonical_seed_regressions=sum(best['rows'][p]['N']>g.caps[p] for p in texts),complete=True)
        assert out['opportunity_count']==1799+249+4*249
    except BaseException as error:
        out.update(failure_type=type(error).__name__,failed_phase=phase);raise
    finally:
        out.update(elapsed=time.monotonic()-started,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        (HERE/'synthetic-results.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
        signal.setitimer(signal.ITIMER_REAL,0);print(json.dumps(out),flush=True)


if __name__=='__main__':main()
