"""Persistent recognition/artifact request; no candidate execution or query cache."""
import hashlib
import json
import time
from projects.algorithm_solver.catalogue.empirical_recognition import rank, decide

POLICY={'id':'c65-m12','min_cosine':0.65,'min_margin':0.12}

def encoded(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()

def sha(raw):return hashlib.sha256(raw).hexdigest()

class RequestTimer:
    def __init__(self,clock=time.perf_counter):
        self.clock=clock;self.start=clock();self.stages={};self.active=None
    def call(self,name,fn):
        self.active=name;start=self.clock()
        try:return fn()
        finally:self.stages[name]=self.clock()-start
    def finish(self):
        return dict(self.stages,end_to_end=self.clock()-self.start)


def materialize(service,pid,selections,timer):
    """Use existing live per-open gate and exact receipt/hash-bound materializer."""
    artifacts={};summary={}
    for language in ('javascript','python'):
        def load():
            answer=service.request(pid,language=language,include_source=True)
            if answer.get('status')!='matched':return None
            artifact=answer.get('artifact',{});selection=answer.get('consumer_selection',{})
            expected=selections[language]
            if selection!=expected or artifact.get('status')!='materialized':
                raise ValueError('exact selected implementation changed during materialization')
            impl=expected['implementation'];raw=artifact['source_utf8'].encode('utf-8')
            if (artifact.get('language')!=language or artifact.get('bytes')!=len(raw) or
                artifact.get('source_sha256')!=impl['source_sha256'] or sha(raw)!=impl['source_sha256']):
                raise ValueError('materialized bytes differ from selected source')
            return artifact,{'source_sha256':sha(raw),'bytes':len(raw),'receipt_sha256':impl['receipt_sha256']}
        loaded=timer.call('materialize_'+language,load)
        if loaded is None:return None,{'status':'abstain','reason':'artifact_unavailable','language':language}
        artifacts[language],summary[language]=loaded
    return artifacts,summary


def request(service,*,mode,ids,encoder=None,index=None,text=None,problem_id=None,clock=time.perf_counter):
    """Serialize actual source-bearing success in memory; report only its hash/size.

    Tests inject synthetic adapters; native runner supplies only pinned instances.
    All status rows carry complete executed-stage costs, including errors/abstains.
    """
    timer=RequestTimer(clock);summary={};response=None
    try:
        if mode=='description':
            if len(ids)!=4081 or len(set(ids))!=4081:raise ValueError('full4081 universe required')
            vector=timer.call('query_encoding',lambda:encoder.encode([text],query=True))
            info=encoder.last_request_info
            if not isinstance(info,dict) or info.get('rows')!=1 or len(info.get('truncated',[]))!=1 or type(info['truncated'][0]) is not bool:
                raise ValueError('exact request truncation metadata required')
            def ranking():
                scores=index.scores(vector)
                return rank(scores,ids)
            ranked=timer.call('full_population_ranking',ranking)
            decision=timer.call('empirical_decision_and_metadata',lambda:decide(ranked,POLICY,service,truncated=info['truncated'][0]))
            summary={'query_sha256':sha(text.encode()),'token_counts_before_truncation':info.get('token_counts_before_truncation'),
                     'truncated':info['truncated'][0],'population':len(ids)}
            if decision['status']!='accepted':
                response={'status':'abstain','reason':decision['reason'],'clarification_questions':[]}
            else:
                problem_id=decision['problem_id'];selections=decision['implementations']
        elif mode=='exact-id-artifact':
            if problem_id not in ('leetcode:802','leetcode:875','leetcode:2406'):raise ValueError('exact control ID out of scope')
            def retrieve():
                selections={}
                for language in ('javascript','python'):
                    value=service.request(problem_id,language=language,include_source=False)
                    if value.get('status')!='matched' or value.get('consumer_selection',{}).get('status')!='selected':return None
                    selections[language]=value['consumer_selection']
                return selections
            selections=timer.call('exact_id_metadata',retrieve)
            if selections is None:response={'status':'abstain','reason':'exact_id_not_qualified','clarification_questions':[]}
        else:raise ValueError('unsupported mode; execution is a separate experiment')
        if response is None:
            artifacts,artifact_summary=materialize(service,problem_id,selections,timer)
            if artifacts is None:
                response=dict(artifact_summary,clarification_questions=[])
            else:
                summary['artifacts']=artifact_summary
                response={'status':'artifact_returned','problem_id':problem_id,'artifacts':artifacts,'clarification_questions':[]}
        wire=timer.call('response_serialization',lambda:encoded(response))
        result=dict(summary,status=response['status'],reason=response.get('reason'),problem_id=problem_id if response['status']=='artifact_returned' else None,
                    response_sha256=sha(wire),response_bytes=len(wire))
    except (TimeoutError, KeyboardInterrupt, SystemExit):
        raise
    except Exception as error:
        # Never publish exception strings that could contain source bytes.
        result=dict(summary,status='error',error_type=type(error).__name__,failed_stage=timer.active)
    return dict(result,mode=mode,timing_seconds=timer.finish(),candidate_executions=0,
                recognition_qualified=False,goal_1c_qualified=False,clarification_questions=[])
