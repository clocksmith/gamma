"""Bounded exact direct moves; supplied-input only, preserving the synthetic core."""
import time
import mechanism


class SearchStop(Exception):
    pass


class CheckedGraph(mechanism.Graph):
    def __init__(self,*args,check=lambda:None,decoder_bytes=0,**kwargs):
        assert type(decoder_bytes) is int and decoder_bytes>=0
        self.decoder_bytes=decoder_bytes;self.check=check;self.audit=None;check();super().__init__(*args,**kwargs);check()

    def summarize(self,*args,**kwargs):
        result=super().summarize(*args,**kwargs)
        result['package_with_decoder_sources']=result['package_bytes']+self.decoder_bytes
        result['objective']=(result['F'],result['N'],result['package_with_decoder_sources'])
        return result

    def path(self,pid,active):
        self.check()
        row=super().path(pid,active)
        if self.audit is not None:
            self.audit['recomputed_programs']+=1
            if row is None:self.audit['failed_pid']=pid
        self.check();return row


def execute(graph,seed,limits,emit,retain,clock=time.monotonic):
    """retain writes only sorted dictionary + scalar metadata, never a plan cache."""
    mechanism.require_checks();current=graph.initial(seed)
    started=clock();deadline=started+limits['seconds'];attempted=completed=0
    counters={k:{'attempted':0,'completed':0,'coverage_failures':0,'recomputed_programs':0}
              for k in ('add','rank','remove','swap','rescore')}
    sweep_no=0;retained=0;stop=None;trace_no=0;accepted=[]
    def event(row):
        nonlocal trace_no
        row={'event_no':trace_no,**row,'seconds':clock()-started};trace_no+=1;emit(row);return row
    def check_time():
        if clock()>=deadline:raise SearchStop('time_limit')
    graph.check=check_time
    def probe(kind,sweep,add=(),remove=(),candidate=None):
        nonlocal attempted,completed,stop
        try:
            check_time()
            if attempted>=limits['evaluations']:raise SearchStop('evaluation_limit')
        except SearchStop as error:stop=str(error);return None,None
        evaluation=attempted;attempted+=1;counters[kind]['attempted']+=1
        if candidate is None:
            affected=set().union(*(graph.owners[w] for w in add)) if add else set()
            affected.update(pid for pid,row in current['rows'].items() if row['used']&set(remove))
        else:affected=set(graph.texts)
        audit={'recomputed_programs':0,'failed_pid':None};graph.audit=audit
        row={'event':'evaluation','evaluation':evaluation,'sweep':sweep,'kind':kind,
             'add':[graph.ids[w] for w in add],'remove':[graph.ids[w] for w in remove],
             'candidate':None if candidate is None else [graph.ids[w] for w in sorted(candidate['active'])],
             'affected_programs':len(affected),'complete':False}
        result=None
        try:
            if kind=='rescore':result=graph.initial(candidate['active'])
            else:result,_=graph.evaluate(current,add,remove,ranking=kind=='rank')
            check_time();row['complete']=True;completed+=1;counters[kind]['completed']+=1
            if result is None:
                row['outcome']='coverage_failure';counters[kind]['coverage_failures']+=1
            else:
                row.update(outcome='feasible' if result['eligible'] else 'ranking_only',F=result['F'],C=result['C'],N=result['N'],
                           package_bytes=result['package_bytes'],objective=list(result['objective']))
        except SearchStop as error:stop=str(error);row['outcome']='interrupted';result=None
        finally:
            graph.audit=None;row.update(audit);counters[kind]['recomputed_programs']+=audit['recomputed_programs'];event(row)
        return result,evaluation
    identity=retain(current,0)
    event({'event':'start','seed':identity,'objective':list(current['objective']),
           'seed_entries':len(current['active']),'free_slots':graph.capacity-len(current['active'])})
    def sweep(kind,iteration,phase,moves,best,origin,rescore,shortlist=()):
        nonlocal sweep_no
        sid=sweep_no;sweep_no+=1;count=0;done=0;start_attempted=attempted
        event({'event':'sweep_start','sweep':sid,'phase':phase,'iteration':iteration,'kind':kind,
               'opportunities':len(moves),'shortlist':[graph.ids[w] for w in shortlist]})
        scores=[]
        for add,remove in moves:
            before=attempted;trial,evaluation=probe(kind,sid,add,remove)
            if attempted>before:count+=1
            if stop:break
            done+=1
            if trial is None:continue
            if kind in ('add','rank'):scores.append((trial['objective'],graph.ids[add[0]],add[0]))
            if trial['eligible'] and (trial['objective'],trial['order'])<(best['objective'],best['order']) and trial['objective']<current['objective']:
                checked,recheck=probe('rescore',sid,candidate=trial)
                if stop:break
                assert checked is not None and checked['objective']==trial['objective'] and checked['active']==trial['active']
                best,origin,rescore=checked,evaluation,recheck
        event({'event':'sweep_end','sweep':sid,'attempted_probes':count,'completed_probes':done,
               'all_evaluations':attempted-start_attempted,'complete':stop is None and done==len(moves),
               'stop':stop})
        return best,origin,rescore,scores
    def accept(best,origin,rescore,partial):
        nonlocal current,retained
        if best['objective']>=current['objective']:return False
        old=current;current=graph.accept(current,best);retained+=1;identity=retain(current,retained)
        row=event({'event':'accept','incumbent':retained,'origin_evaluation':origin,'rescore_evaluation':rescore,
                   'before':list(old['objective']),'after':list(current['objective']),'identity':identity,'partial_sweep':partial})
        accepted.append({k:row[k] for k in ('incumbent','origin_evaluation','rescore_evaluation','before','after','identity','partial_sweep')})
        return True
    free=graph.capacity-len(current['active'])
    assert free==limits['expected_free_slots']
    for iteration in range(free):
        moves=[((word,),()) for word in graph.pool if word not in current['active']]
        best,origin,rescore,_=sweep('add',iteration,'A',moves,current,None,None)
        changed=accept(best,origin,rescore,stop is not None)
        if stop or not changed:break
    epochs=0
    if stop is None:
        for iteration in range(limits['epochs']):
            epochs+=1;best=current;origin=rescore=None
            additions=[((word,),()) for word in graph.pool if word not in current['active']]
            kind='rank' if len(current['active'])==graph.capacity else 'add'
            best,origin,rescore,scores=sweep(kind,iteration,'B',additions,best,origin,rescore)
            shortlist=[word for _,_,word in sorted(scores)[:limits['shortlist']]]
            if stop is None:
                removals=[((),(word,)) for word in sorted(current['active'])]
                best,origin,rescore,_=sweep('remove',iteration,'B',removals,best,origin,rescore)
            if stop is None:
                swaps=[((add,),(remove,)) for add in shortlist for remove in sorted(current['active'])]
                best,origin,rescore,_=sweep('swap',iteration,'B',swaps,best,origin,rescore,shortlist)
            changed=accept(best,origin,rescore,stop is not None)
            if stop:break
            if not changed:stop='no_improving_evaluated_neighbor';break
        else:stop='epoch_limit'
    if stop is None:stop='epoch_limit'
    result={'stop':stop,'attempted':attempted,'completed':completed,'counters':counters,'sweeps':sweep_no,
            'exchange_epochs_started':epochs,'accepted':accepted,'final_incumbent':retained,
            'initial_free_slots':free,'seconds':clock()-started,'final_objective':list(current['objective'])}
    event({'event':'stop',**result})
    graph.check=lambda:None
    result['seconds']=clock()-started
    result['soft_overrun_seconds']=max(0.,result['seconds']-limits['seconds'])
    return current,result
