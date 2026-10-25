"""Known-ID retrieval -> input admission -> isolated execution -> verification -> response.

The executor and verifier are operator-bound trusted adapters, never query fields.
This mechanism does not recognize informal language or broaden admitted contracts.
"""
import hashlib
import json
import time


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def request(service, problem_id, language, args, *, source_sha256, admit, execute, verify):
    start=time.perf_counter(); answer=service.request(problem_id,language=language,include_source=True)
    if answer.get('status')!='matched':
        return {'status':'abstained','stage':'retrieval','candidate_executions':0}
    artifact=answer.get('artifact',{}); source=artifact.get('source_utf8','').encode()
    if artifact.get('source_sha256')!=source_sha256 or hashlib.sha256(source).hexdigest()!=source_sha256:
        raise ValueError('source identity changed')
    retrieved=time.perf_counter()
    # Deliberately before handing any candidate source/argument to the executor.
    admit(args,answer); admitted=time.perf_counter()
    observation=execute(source,args); executed=time.perf_counter()
    value=verify(args,observation); verified=time.perf_counter()
    response=encode({'status':'verified','result':value}); served=time.perf_counter()
    return {'status':'verified','candidate_executions':1,'source_sha256':source_sha256,
            'response_sha256':hashlib.sha256(response).hexdigest(),'response_bytes':len(response),
            'timing_seconds':{'retrieval_and_hash':retrieved-start,'input_admission':admitted-retrieved,
             'isolated_execution':executed-admitted,'verification':verified-executed,
             'response_serialization':served-verified,'end_to_end':served-start}}
