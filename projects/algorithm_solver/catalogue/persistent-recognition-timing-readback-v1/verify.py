"""Independent readback consistency, not clock attestation or model/source replay."""
import argparse,hashlib,json,math,re
from pathlib import Path
HASH=re.compile(r'[0-9a-f]{64}\Z')

def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def number(x):return type(x)in(int,float)and math.isfinite(x)and x>=0

def validate(freeze,report,supervisor,rows,progress,freeze_sha):
    def require(value,why):
        if not value:raise ValueError(why)
    require(report['freeze_sha256']==supervisor['freeze_sha256']==freeze_sha,'freeze identity')
    require(report['status']==supervisor['status']==progress['status']=='completed','terminal status')
    require(supervisor['exit_code']==0 and supervisor['error_type']is None and supervisor['wall_timeout']is False and supervisor['termination_signals']==[],'supervisor outcome')
    cleanup=supervisor['owned_group_cleanup']
    require(cleanup['leader_reaped']is True and cleanup['live_members']==[] and cleanup['inspection_unreadable_pids']==[] and cleanup['no_executing_group_members_observed']is True,'owned group cleanup evidence')
    require(type(cleanup['process_group_id'])is int and cleanup['process_group_id']>0,'owned group identity')
    require(rows==report['requests'] and len(rows)==14 and progress['completed_requests']==14,'incremental/final agreement')
    require(report['description_requests']==8 and report['exact_id_requests']==6,'mode counts')
    require(freeze['policy']=={'id':'c65-m12','min_cosine':.65,'min_margin':.12},'frozen policy')
    require(len(freeze['stable_ids'])==4081 and len(set(freeze['stable_ids']))==4081,'population')
    counts={s:sum(r['status']==s for r in rows)for s in ('abstain','artifact_returned','error')}
    require(sum(counts.values())==14 and counts==report['status_counts']==progress['status_counts'],'status counts')
    for i,row in enumerate(rows):
        require(row['candidate_executions']==0 and row['recognition_qualified']is False and row['goal_1c_qualified']is False and row['clarification_questions']==[],'row evidence class')
        timing=row['timing_seconds'];require('end_to_end'in timing and all(number(v)for v in timing.values()),'finite nonnegative stage timing')
        require(sum(v for k,v in timing.items()if k!='end_to_end')<=timing['end_to_end']+1e-8,'stage sum exceeds whole request')
        if i<8:
            position=i%4;pass_index=i//4;q=freeze['query_selection'][position]
            require(row['mode']=='description' and row['query_position']==position and row['pass_index']==pass_index and row['query_id']==q['query_id'],'description order')
            require(row['cold_process_first_query']==(i==0),'cold first marker')
            if row['status']!='error':
                require(row['population']==4081 and row['query_sha256']==q['text_sha256'],'query/population identity')
                require({'query_encoding','full_population_ranking','empirical_decision_and_metadata','response_serialization'}<=set(timing),'description cost scope')
        else:
            require(row['mode']=='exact-id-artifact' and row['pass_index']==(i-8)//3 and row['control_id']==freeze['exact_ids'][(i-8)%3],'exact control order')
            require('query_encoding'not in timing and 'full_population_ranking'not in timing,'exact-ID must not claim recognition')
        if row['status']=='error':require(bool(row.get('error_type')),'error evidence')
        else:
            require(HASH.fullmatch(row['response_sha256'])and type(row['response_bytes'])is int and row['response_bytes']>0,'response hash/byte evidence')
            require('response_serialization'in timing,'serialization cost')
        if row['status']=='artifact_returned':
            require(set(row['artifacts'])=={'javascript','python'},'dual artifact metadata')
            for language,artifact in row['artifacts'].items():
                require(HASH.fullmatch(artifact['source_sha256'])and HASH.fullmatch(artifact['receipt_sha256'])and artifact['bytes']>0,'artifact hash/receipt evidence')
                require('materialize_'+language in timing,'materialization cost')
            require(row['response_bytes']>=sum(a['bytes']for a in row['artifacts'].values()),'source-bearing response byte count')
        if row['mode']=='description' and row['status']=='abstain' and row['reason']=='empirical_confidence_threshold':
            response={'status':'abstain','reason':row['reason'],'clarification_questions':[]}
            require(row['response_sha256']==sha(encoded(response))and row['response_bytes']==len(encoded(response)),'reconstructable abstention response hash')
    init=report['initialization_seconds'];require(all(number(v)for v in init.values()),'initialization timing')
    require(sum(v for k,v in init.items()if k!='all_initialization')<=init['all_initialization']+1e-8,'initialization subtotal')
    expected=init['all_initialization']+rows[0]['timing_seconds']['end_to_end']
    require(abs(expected-report['first_query_plus_initialization_seconds'])<=1e-8,'cold arithmetic')
    require(report['second_pass_description_seconds']==[r['timing_seconds']['end_to_end']for r in rows[:8]if r['pass_index']==1],'warm arithmetic')
    require(number(report['wall_seconds'])and init['all_initialization']+sum(r['timing_seconds']['end_to_end']for r in rows)<=report['wall_seconds']+1e-8,'run timing coverage')
    require(number(report['module_start_to_report_seconds'])and report['module_start_to_report_seconds']>=report['wall_seconds'],'module timer ordering')
    require(number(supervisor['wall_seconds'])and supervisor['wall_seconds']>=report['module_start_to_report_seconds'],'supervisor timer ordering')
    require(number(report['cpu_seconds'])and report['cpu_seconds']<=300,'reported CPU budget')
    require(report['candidate_executions']==0 and report['confirmation_read']is False and report['query_vector_cache']is False and report['source_availability_ranking_filter']is False,'scope exclusions')
    require(report['recognition_qualified']is False and report['goal_1c_qualified']is False and report['source_bytes_published']is False,'qualification/source boundary')
    require('source_utf8'not in json.dumps(report),'raw source in report')
    return {'status':'consistent_readback','status_counts':counts,'description_artifact_successes':sum(r['status']=='artifact_returned'for r in rows[:8]),
            'description_abstentions':sum(r['status']=='abstain'for r in rows[:8]),'exact_id_artifact_successes':sum(r['status']=='artifact_returned'for r in rows[8:]),
            'first_query_plus_initialization_seconds':expected,'second_pass_description_seconds':report['second_pass_description_seconds'],
            'scope':'Independent identity/count/status/stage arithmetic/response-hash presence/recorded cleanup consistency. Not independent clock attestation, fresh encoding attestation, source-byte rehash or candidate correctness.',
            'recognition_qualified':False,'goal_1c_qualified':False,'source_reads':0,'model_runs':0}

def run(args):
    root=Path(args.input);freeze_raw=Path(args.freeze).read_bytes()
    if sha(freeze_raw)!=args.freeze_sha256:raise ValueError('freeze bytes changed')
    artifacts={name:(root/name).read_bytes()for name in ('supervisor.json','results/report.json','results/requests.jsonl','results/progress.json')}
    report=json.loads(artifacts['results/report.json']);supervisor=json.loads(artifacts['supervisor.json']);rows=[json.loads(x)for x in artifacts['results/requests.jsonl'].splitlines()];progress=json.loads(artifacts['results/progress.json'])
    result=validate(json.loads(freeze_raw),report,supervisor,rows,progress,args.freeze_sha256)
    result.update(schema='gamma.persistent-recognition-independent-readback.v1',freeze_sha256=args.freeze_sha256,
                  input_sha256={name:sha(raw)for name,raw in artifacts.items()},verifier_sha256=sha(Path(__file__).read_bytes()))
    Path(args.output).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('input','freeze','freeze-sha256','output'):p.add_argument('--'+name,required=True)
    run(p.parse_args())
