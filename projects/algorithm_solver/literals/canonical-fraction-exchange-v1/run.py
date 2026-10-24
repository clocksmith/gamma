"""Activated fixed-fit canonical fraction worker; no validation or source execution."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import time
import common as c
import codec
import search

WHOLE_SECONDS=1200
class WholeJobTimeout(BaseException):pass


def arm(cohort,work,output,deadline):
    c.require_checks();started=time.monotonic();phase='preflight';folder=output/cohort;writable=False
    def expired(*_):raise WholeJobTimeout('whole-worker deadline')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,max(.001,min(WHOLE_SECONDS,deadline-started)))
    def hard_check():
        if time.monotonic()>=deadline:raise WholeJobTimeout('whole-worker deadline')
    try:
        resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,)*2);os.sched_setaffinity(0,{'R':{4},'naming':{5}}[cohort])
        folder.mkdir();writable=True;contract=json.loads((c.HERE/'contract.json').read_text())
        assert contract['limits']['production_seconds']==WHOLE_SECONDS and contract['limits']['address_space_bytes']==8*1024**3
        assert contract['limits']['arm_cores']=={'R':[4],'naming':[5]} and 0<deadline-started<=WHOLE_SECONDS
        c.check_contract(contract,work);phase='input_pool_replay';inputs=c.load_cohort(contract,work,cohort);hard_check()
        phase='graph';clock=time.monotonic()
        graph=search.CheckedGraph(inputs['texts'],inputs['candidates'],inputs['seed'],capacity=contract['pool']['capacity'],
                  banned=inputs['bans'],check=hard_check,decoder_bytes=contract['decoder_dependency_bytes'],**contract['construction'])
        assert graph.arcs==inputs['parent_arm']['arcs'] and graph.transitions==inputs['parent_arm']['transitions']
        caps={pid:{'source_sha256':hashlib.sha256(text.encode()).hexdigest(),'N':graph.caps[pid]} for pid,text in graph.texts.items()}
        assert caps==contract['canonical_seed_caps'][cohort]
        public=json.loads((c.LIT/contract['canonical_parent_evidence']).read_text())
        parent=next(a for a in public['arms'] if a['cohort']==cohort);seed=parent['witnesses']['seed']['canonical_min_N']
        assert parent['source_sha256']==inputs['bindings']['source_sha256']
        seed_vocab=sorted(inputs['seed']);dense={w:i for i,w in enumerate(seed_vocab)}
        dictionary_digest=hashlib.sha256(codec.dictionary_bytes(seed_vocab)).digest()
        for pid,row in graph.seed['rows'].items():
            hard_check();prior=seed['per_problem'][pid]
            packet=b'LTV1\x08'+dictionary_digest+row['N'].to_bytes(4,'big')+bytes(dense[w] for w in row['words'])
            assert (caps[pid]['source_sha256'],row['N'],row['C'],hashlib.sha256(packet).hexdigest())==(prior['source_sha256'],prior['N'],prior['C'],prior['packet_sha256'])
        c.write(folder/'seed-caps.json',caps)
        build_seconds=time.monotonic()-clock;(folder/'retained-dictionaries').mkdir();retained=[]
        def retain(state,index):
            hard_check();assert index==len(retained) and state['eligible']
            path=folder/'retained-dictionaries'/f'{index:03d}.json';c.write(path,sorted(state['active']))
            identity={'index':index,'dictionary_sha256':c.sha(path)};retained.append(identity);return identity
        phase='search'
        with (folder/'trace.jsonl').open('w') as trace:
            def emit(row):trace.write(json.dumps(row,sort_keys=True)+'\n');trace.flush()
            final,summary=search.execute(graph,inputs['seed'],contract['search'],emit,retain)
        assert summary['final_incumbent']==len(retained)-1 and summary['attempted']<=contract['search']['evaluations']
        phase='witnesses';clock=time.monotonic();graph.check=hard_check;incumbents=[]
        (folder/'incumbents').mkdir()
        for identity in retained:
            hard_check();index=identity['index'];vocab=json.loads((folder/'retained-dictionaries'/f'{index:03d}.json').read_text())
            witness=codec.measure(graph,vocab,folder/'incumbents'/f'{index:03d}',contract['decoder_dependency_bytes'],check=hard_check)
            assert witness['dictionary_sha256']==identity['dictionary_sha256'];incumbents.append({'index':index,'witness':witness})
        assert summary['final_score']==incumbents[-1]['witness']['score']==search.score(final)
        for pid,row in incumbents[0]['witness']['per_problem'].items():
            prior=seed['per_problem'][pid]
            assert (row['source_sha256'],row['selections'],row['characters'],row['packet_sha256'])==(prior['source_sha256'],prior['N'],prior['C'],prior['packet_sha256'])
        witness_seconds=time.monotonic()-clock;hard_check()
        result={'cohort':cohort,'complete':True,'validation_loaded':False,'fit_problems':len(inputs['texts']),
                'bindings':inputs['bindings'],'pool_counts':inputs['pool_counts'],'original_seed_hash':inputs['original_reference_hashes']['seed'],
                'seed_caps_sha256':c.sha(folder/'seed-caps.json'),'incumbents':incumbents,'final_incumbent':summary['final_incumbent'],
                'search':summary,'trace_sha256':c.sha(folder/'trace.jsonl'),'arcs':graph.arcs,'transitions':graph.transitions,
                'build_seconds':build_seconds,'witness_seconds':witness_seconds,'contract_sha256':c.sha(c.HERE/'contract.json'),
                'seconds':time.monotonic()-started,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        c.number(result['seconds'],WHOLE_SECONDS);c.write(folder/'results.json',result);c.write(folder/'status.json',{'complete':True,'phase':'complete'})
    except BaseException as error:
        if writable or not folder.exists():
            (folder/'results.json').unlink(missing_ok=True)
            c.write(folder/'failure.json',{'complete':False,'validation_loaded':False,'phase':phase,'exception':type(error).__name__,
                    'seconds':time.monotonic()-started,'partial_witnesses_promoted':False})
        raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--cohort',choices=('R','naming'),required=True)
    ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--deadline',type=float,required=True);a=ap.parse_args();arm(a.cohort,a.work,a.output,a.deadline)
