"""Fit-only conditional character slots, matched repairs, then unchanged-source decoding."""
import argparse
from collections import Counter
import concurrent.futures
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import platform
import random
import sys
import time
import repair
HERE=repair.HERE;LIT=repair.LIT;analyze=repair.analyze

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

sel=module('character_slots_selection',LIT/'lagrange-select-v2/selection.py')
tail=module('character_slots_tail',LIT/'tail-search-v1/search.py')


def ordered(vocab):
    return [s for s in repair.ALPHABET if s in vocab]+sorted(s for s in set(vocab) if len(s)>1)


def pool_rank(texts,banned,length):
    pool=sel.build_pool(texts,banned,length);lookup=set(pool);counts=Counter()
    for text in texts.values():
        for i in range(len(text)):
            for n in range(2,min(length,len(text)-i)+1):
                word=text[i:i+n]
                if word in lookup:counts[word]+=1
    return pool,sorted(pool,key=lambda s:(-counts[s]*(len(s)-1),s))


def fit_arm(job):
    name,work,out,c,cores=job;work=Path(work);out=Path(out);os.sched_setaffinity(0,set(cores))
    root=work/c['seed_relative_path'];fit=json.loads((root/'fit-sources.json').read_text())
    assert set(fit)=={str(i) for i in c['partition']['dev_fit']}
    vocab=json.loads((root/'dictionary.json').read_text());assert vocab==ordered(vocab)
    initial,_,usage=repair.exact(fit,vocab);observed=set(''.join(fit.values()));reserved=set(repair.ALPHABET)-observed
    assert observed<=set(repair.ALPHABET)
    banned=sel.forbidden_strings(fit);assert not set(vocab)&banned
    folder=out/name;folder.mkdir();started=time.monotonic();moves=[];cfg=c['search'];best=initial
    pool,ranked=pool_rank(fit,banned,cfg['max_length']);analyze.write(folder/'pool.json',pool)
    pool_hash=analyze.sha((folder/'pool.json').read_bytes());rng=random.Random(cfg['seed']);stop='move_limit'
    for no in range(cfg['moves']):
        remaining=cfg['seconds']-(time.monotonic()-started)
        if remaining<=0:stop='time_limit';break
        fixed,candidates,capacity,freed=repair.proposal(vocab,observed,reserved,pool,ranked,rng,name,cfg,usage)
        chosen,solver=repair.solve(fit,fixed,candidates,capacity,min(cfg['solver_seconds'],remaining));trial=ordered(fixed+chosen)
        assert len(trial)==len(set(trial))<=256 and reserved<=set(trial) and not set(trial)&banned
        score=rows=newusage=None
        if solver['feasible']:
            score,rows,newusage=repair.exact(fit,trial)  # missing coverage fails here, never a free character arc
            assert score<=solver['objective']+1e-6
            if solver['status']==0:assert abs(score-solver['objective'])<=1e-6
        before=best;accepted=score is not None and score<best
        record={'move':no,**solver,**freed,'capacity':capacity,'candidate_count':len(candidates),'exact':score,
                'accepted':accepted,'before':before,'validation_loaded':False,'pool_sha256':pool_hash}
        if accepted:
            vocab,best,usage=trial,score,newusage
            analyze.write(folder/f'incumbent-{no:02d}.json',vocab)
            record['dictionary_sha256']=analyze.sha((folder/f'incumbent-{no:02d}.json').read_bytes())
        record.update(incumbent=best,character_entries=sum(len(s)==1 for s in vocab),learned_entries=sum(len(s)>1 for s in vocab))
        moves.append(record)
        with (folder/'moves.jsonl').open('a') as f:f.write(json.dumps(record,sort_keys=True)+'\n')
        print(json.dumps({'arm':name,**record}),flush=True)
    analyze.write(folder/'dictionary.json',vocab)
    analyze.write(folder/'fit-seal.json',{'validation_loaded':False,'dictionary_sha256':analyze.sha((folder/'dictionary.json').read_bytes()),
                   'fit_source_sha256':c['private_files'][c['seed_relative_path']+'/fit-sources.json'],'pool_sha256':pool_hash})
    result={'arm':name,'initial_fit_selections':initial,'fit_selections':best,'pool_entries':len(pool),'pool_sha256':pool_hash,
            'observed_character_count':len(observed),'reserved_unseen_character_count':len(reserved),'moves':moves,'stop':stop,'seconds':time.monotonic()-started,
            'fit_seal_sha256':analyze.sha((folder/'fit-seal.json').read_bytes())}
    analyze.write(folder/'fit-summary.json',result);return result


def main(work,out):
    c=json.loads((HERE/'contract.json').read_text());import numpy,scipy
    assert Path(sys.executable).absolute()==Path(c['python_bin']).absolute()
    assert c['versions']=={'python':platform.python_version(),'numpy':numpy.__version__,'scipy':scipy.__version__}
    assert os.environ.get('OMP_NUM_THREADS')==os.environ.get('OPENBLAS_NUM_THREADS')=='2'
    for rel,h in c['code_hashes'].items():assert analyze.sha((LIT/rel).read_bytes())==h,rel
    for rel,h in c['private_files'].items():assert analyze.sha((work/rel).read_bytes())==h,rel
    for path,h in c['runtime_files'].items():assert analyze.sha(Path(path).read_bytes())==h,path
    out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    jobs=[(n,str(work.resolve()),str(out.resolve()),c,cores) for n,cores in zip(('fixed96','optional'),c['cores'])]
    with concurrent.futures.ProcessPoolExecutor(max_workers=2,mp_context=multiprocessing.get_context('spawn')) as pool:summaries=list(pool.map(fit_arm,jobs))
    analyze.write(out/'all-fit-sealed.json',{'validation_loaded':False,'summaries':summaries})
    # Only now consume validation values. The source/qualification identity was already pinned.
    root=work/c['seed_relative_path'];sources=json.loads((root/'sources.json').read_text());baseline=json.loads((root/'dictionary.json').read_text())
    proof=json.loads((LIT/'lns-naming-v1/evidence/results.json').read_text());proof=next(a for a in proof['arms'] if a['arm']=='seed_fixed_seed')
    assert set(sources)=={str(i) for group in c['partition'].values() for i in group}
    assert all(q['passed'] for q in proof['qualification'].values())
    for pid,text in sources.items():assert analyze.sha(text.encode())==proof['per_problem'][pid]['source_sha256']
    banned=sel.forbidden_strings(sources);results=[]
    (out/'seed').mkdir();analyze.write(out/'seed/dictionary.json',baseline)
    for name in ('seed','fixed96','optional'):
        folder=out/name;vocab=json.loads((folder/'dictionary.json').read_text());rows,illegal=tail.evaluate_output(sources,vocab,8,banned)
        db=analyze.dictionary_bytes(vocab);(folder/'dictionary.bin').write_bytes(db);(folder/'packets').mkdir()
        for pid,row in rows.items():
            row.update(qualified_source=proof['qualification'][pid]['passed'],source_bytes=len(sources[pid].encode()))
            if row['encodable']:
                seq=analyze.shortest_encode(sources[pid],vocab);packet=analyze.encode(vocab,seq,8);assert analyze.decode(db,packet)==sources[pid]
                row['packet_sha256']=analyze.sha(packet);(folder/'packets'/f'{pid}.bin').write_bytes(packet)
        a={'arm':name,'width':8,'entries':len(vocab),'character_entries':sum(len(s)==1 for s in vocab),'learned_entries':sum(len(s)>1 for s in vocab),
           'dictionary_sha256':analyze.sha((folder/'dictionary.json').read_bytes()),'dictionary_bytes':len(db),'per_problem':rows,'illegal_entry_sha256':illegal,
           'qualification_reused_from':c['qualification_evidence_sha256'],
           'search':next((s for s in summaries if s['arm']==name),None)}
        for split,key in [('fit','dev_fit'),('validation','dev_val')]:
            ids=c['partition'][key];d=tail.aggregate(rows,ids,len(db));good=[rows[str(i)] for i in ids if rows[str(i)]['encodable']]
            d.update(qualified=len(good),source_bytes=sum(rows[str(i)]['source_bytes'] for i in ids),single_character_codes=sum(r['single_characters'] for r in good),
                     package_with_decoder_dependencies=d['package_bytes']+c['decoder_dependency_bytes'],framing_bytes=41*len(good),
                     payload_bits=8*sum(r['selections'] for r in good),padding_bits=0)
            a[split]=d
        assert a['fit']['covered']==300
        if a['search']:assert a['fit']['selections']['total']==a['search']['fit_selections']
        results.append(a)
    analyze.write(out/'results.json',{'arms':results,'contract_sha256':analyze.sha((HERE/'contract.json').read_bytes()),'seconds':time.monotonic()-started,
        'decoded_packets':sum(a['fit']['covered']+a['validation']['covered'] for a in results)})
    print(json.dumps({'complete':True,'coverage':{a['arm']:a['validation']['covered'] for a in results}}),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();main(a.work,a.output)
