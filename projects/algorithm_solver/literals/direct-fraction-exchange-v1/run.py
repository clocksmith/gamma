"""Activated direct search worker; all population access follows hard guards."""
import argparse
import json
import os
from pathlib import Path
import resource
import signal
import time
import common as c
import search

WHOLE_SECONDS=1200


class WholeJobTimeout(BaseException):
    pass


def arm(cohort,work,output,deadline):
    c.require_checks();started=time.monotonic();phase='preflight';folder=output/cohort
    def expired(*_):raise WholeJobTimeout('whole-worker deadline')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,max(.001,min(WHOLE_SECONDS,deadline-started)))
    def hard_check():
        if time.monotonic()>=deadline:raise WholeJobTimeout('whole-worker deadline')
    try:
        resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,)*2)
        os.sched_setaffinity(0,{'R':{6},'naming':{7}}[cohort])
        folder.mkdir();contract=json.loads((c.HERE/'contract.json').read_text())
        assert contract['limits']['production_seconds']==WHOLE_SECONDS
        assert contract['limits']['address_space_bytes']==8*1024**3
        assert contract['limits']['arm_cores']=={'R':[6],'naming':[7]}
        assert 0<deadline-started<=contract['limits']['production_seconds']
        c.check_contract(contract,work);phase='input_pool_replay';hard_check()
        inputs=c.load_cohort(contract,work,cohort);hard_check();phase='graph';clock=time.monotonic()
        graph=search.CheckedGraph(inputs['texts'],inputs['candidates'],contract['pool']['capacity'],inputs['bans'],
                                  check=hard_check,decoder_bytes=contract['decoder_dependency_bytes'],**contract['construction'])
        assert graph.arcs==inputs['parent_arm']['arcs'] and graph.transitions==inputs['parent_arm']['transitions']
        build_seconds=time.monotonic()-clock
        (folder/'retained-dictionaries').mkdir();retained=[]
        def retain(state,index):
            assert index==len(retained) and state['eligible']
            path=folder/'retained-dictionaries'/f'{index:03d}.json';c.write(path,sorted(state['active']))
            identity={'index':index,'dictionary_sha256':c.sha(path)};retained.append(identity);return identity
        phase='search'
        with (folder/'trace.jsonl').open('w') as trace:
            def emit(row):trace.write(json.dumps(row,sort_keys=True)+'\n');trace.flush()
            final,summary=search.execute(graph,inputs['seed'],contract['search'],emit,retain)
        assert summary['final_incumbent']==len(retained)-1 and summary['attempted']<=contract['search']['evaluations']
        phase='final_independent_rescore';clock=time.monotonic();hard_check()
        independent=search.mechanism.parent.exact(inputs['texts'],sorted(final['active']))
        assert (independent['F'],independent['C'],independent['N'])==(final['F'],final['C'],final['N'])
        hard_check();final_rescore_seconds=time.monotonic()-clock
        phase='witnesses';clock=time.monotonic();references={};incumbents=[]
        (folder/'references').mkdir();(folder/'incumbents').mkdir()
        for name,vocab in inputs['references'].items():
            hard_check();w=c.backend.measure(inputs['texts'],vocab,folder/'references'/name,contract['decoder_dependency_bytes'])
            parent=inputs['parent_arm']['witnesses'][name]
            for key in ('objective','characters','selections','actions','dictionary_bytes','package_bytes','package_with_decoder_sources'):
                assert w[key]==parent[key]
            references[name]=w
        for identity in retained:
            hard_check();index=identity['index'];vocab=json.loads((folder/'retained-dictionaries'/f'{index:03d}.json').read_text())
            witness=c.backend.measure(inputs['texts'],vocab,folder/'incumbents'/f'{index:03d}',contract['decoder_dependency_bytes'])
            assert witness['dictionary_sha256']==identity['dictionary_sha256']
            incumbents.append({'index':index,'witness':witness})
        finalw=incumbents[-1]['witness']
        assert summary['final_objective']==[finalw['objective'],finalw['selections']['total'],finalw['package_with_decoder_sources']]
        assert incumbents[0]['witness']==references['seed']
        witness_seconds=time.monotonic()-clock;hard_check()
        result={'cohort':cohort,'complete':True,'validation_loaded':False,'fit_problems':len(inputs['texts']),
                'bindings':inputs['bindings'],'pool_counts':inputs['pool_counts'],
                'original_reference_hashes':inputs['original_reference_hashes'],'references':references,'incumbents':incumbents,
                'final_incumbent':summary['final_incumbent'],'search':summary,'trace_sha256':c.sha(folder/'trace.jsonl'),
                'arcs':graph.arcs,'transitions':graph.transitions,'build_seconds':build_seconds,
                'final_independent_rescore_seconds':final_rescore_seconds,'witness_seconds':witness_seconds,
                'contract_sha256':c.sha(c.HERE/'contract.json'),'seconds':time.monotonic()-started,
                'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        c.number(result['seconds'],contract['limits']['production_seconds']);c.write(folder/'results.json',result)
        c.write(folder/'status.json',{'complete':True,'phase':'complete'})
    except BaseException as error:
        c.write(folder/'failure.json',{'complete':False,'validation_loaded':False,'phase':phase,'exception':type(error).__name__,
                'seconds':time.monotonic()-started,'partial_witnesses_promoted':False});raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--cohort',choices=('R','naming'),required=True)
    ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--deadline',type=float,required=True);a=ap.parse_args();arm(a.cohort,a.work,a.output,a.deadline)
