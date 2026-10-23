"""Width-explicit matched character-slot repairs on fixed Python sources."""
from collections import Counter,defaultdict
import json
import os
from pathlib import Path
import random
import signal
import time
from common import ALPHABET,analyze,authority,banned,checked,ordered,repair,sha,write,enforce_limits

def proposal(vocab,observed,reserved,pool,ranked,rng,mode,cfg,usage,width):
    assert mode in ('fixed96','optional')
    learned=sorted(s for s in vocab if len(s)>1)
    chars=sorted(s for s in vocab if len(s)==1 and s in observed and s not in reserved)
    drop=[]
    if mode=='optional':
        n=min(cfg['free_characters'],len(chars));head=sorted(chars,key=lambda s:(usage.get(s,0),s))[:min(cfg['priority_characters'],n)]
        drop=head+rng.sample([s for s in chars if s not in head],n-len(head))
    total=cfg['free_total'][str(width)]
    removed=drop+rng.sample(learned,min(total-len(drop),len(learned)))
    fixed=[s for s in vocab if s not in set(removed)];present=set(fixed)
    top=[s for s in ranked if s not in present][:cfg['top']]
    extra=[s for s in rng.sample(pool,min(len(pool),3*cfg['random'])) if s not in present|set(top)][:cfg['random']]
    candidates=list(dict.fromkeys(removed+(sorted(observed-present) if mode=='optional' else [])+top+extra))
    assert reserved<=present and not present&set(candidates)
    if mode=='fixed96':assert set(ALPHABET)<=present
    return fixed,candidates,2**width-len(fixed),{'freed_characters':len(drop),'freed_learned':len(removed)-len(drop)}

def pool_rank(texts,ban,length):
    owners=defaultdict(set);counts=Counter()
    for pid,text in texts.items():
        for i in range(len(text)):
            for n in range(2,min(length,len(text)-i)+1):
                s=text[i:i+n]
                if s not in ban:owners[s].add(pid);counts[s]+=1
    pool=sorted(s for s in owners if len(owners[s])>=2)
    return pool,sorted(pool,key=lambda s:(-counts[s]*(len(s)-1),s))

def fit_arm(job):
    width,mode,out,c,core=job;folder=Path(out)/f'w{width}'/mode;folder.mkdir(parents=True)
    os.sched_setaffinity(0,{core});started=time.monotonic();cfg=c['search'];phase='setup'
    def timeout(*_):raise TimeoutError('arm phase deadline including setup/pool/solver')
    signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,cfg['seconds'])
    try:
        enforce_limits(c)
        inp=c['inputs'][str(width)];texts=checked(inp['fit']);assert set(texts)==set(map(str,c['partition']['dev_fit']))
        authority(c,width,'scope_joint',texts)
        vocab=checked(inp['seed_dictionary']);assert vocab==ordered(vocab) and len(vocab)<=2**width
        observed=set(''.join(texts.values()));reserved=set(ALPHABET)-observed
        assert observed<=set(ALPHABET) and set(ALPHABET)<=set(vocab)
        ban=banned(texts,c['entries']);assert not set(vocab)&ban
        best,_,usage=repair.exact(texts,vocab);initial=best
        write(folder/'dictionary.json',vocab);write(folder/'fit-sources.json',texts)
        phase='pool';pool,ranked=pool_rank(texts,ban,cfg['max_length']);write(folder/'pool.json',pool)
        rng=random.Random(cfg['seed']);moves=[];stop='move_limit';phase='repairs'
        for no in range(cfg['moves']):
            remaining=cfg['seconds']-(time.monotonic()-started)
            # Leave checkpoint/seal headroom; exhausted search is a retained incumbent.
            if remaining<=cfg['checkpoint_reserve_seconds']:stop='time_limit';break
            fixed,candidates,capacity,freed=proposal(vocab,observed,reserved,pool,ranked,rng,mode,cfg,usage,width)
            chosen,solver=repair.solve(texts,fixed,candidates,capacity,min(cfg['solver_seconds'],remaining-cfg['checkpoint_reserve_seconds']))
            trial=ordered(fixed+chosen);score=newusage=None
            if solver['feasible']:
                assert len(trial)<=2**width and reserved<=set(trial) and not set(trial)&ban
                score,_,newusage=repair.exact(texts,trial)
                assert score<=solver['objective']+1e-6
                if solver['status']==0:assert abs(score-solver['objective'])<=1e-6
            accepted=score is not None and score<best
            record={'move':no,**solver,**freed,'capacity':capacity,'candidate_count':len(candidates),'exact':score,'before':best,'accepted':accepted}
            if accepted:vocab,best,usage=trial,score,newusage;write(folder/'dictionary.json',vocab)
            record['incumbent']=best;moves.append(record);write(folder/'moves.json',moves)
        phase='seal'
        seal={'validation_loaded':False,'dictionary_sha256':sha((folder/'dictionary.json').read_bytes()),
              'fit_source_sha256':sha((folder/'fit-sources.json').read_bytes()),'pool_sha256':sha((folder/'pool.json').read_bytes())}
        write(folder/'fit-seal.json',seal)
        summary={'width':width,'arm':mode,'initial_fit_selections':initial,'fit_selections':best,'moves':moves,'stop':stop,
                 'seconds':time.monotonic()-started,'observed_characters':len(observed),'reserved_characters':len(reserved),
                 'fit_seal_sha256':sha((folder/'fit-seal.json').read_bytes())}
        write(folder/'fit-summary.json',summary);return summary
    except BaseException as e:
        write(folder/'failure.json',{'phase':phase,'error_type':type(e).__name__,'error':str(e),'complete':False,'promotion_allowed':False});raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)
