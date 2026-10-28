"""Host-only native3885 bridge; projections never enter candidate packets."""
import importlib.util
import json
from pathlib import Path
S=importlib.util.spec_from_file_location('gamma_m_native_oracles',Path(__file__).with_name('oracles.py'));oracle=importlib.util.module_from_spec(S);S.loader.exec_module(oracle)

def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def packet(pid,cases,*,maximum_bytes):
    if type(pid) is not int or pid!=3885 or type(maximum_bytes) is not int or maximum_bytes<=0 or type(cases) is not list or not cases:raise ValueError('fixed3885 cases and existing positive caller bound required')
    calls=[]
    for row in cases:oracle.validate(pid,row['args']);calls.append({'args':row['args']})
    raw=encoded({'schema':'gamma.native-class-transport.v1','native_problem_id':3885,'calls':calls})
    if len(raw)>maximum_bytes:raise ValueError('native packet exceeds existing caller bound')
    return raw

def projected_record(pid,args,expected,language,index):
    oracle.validate(pid,args)
    if pid!=3885 or language not in ('python','javascript') or type(index) is not int:raise ValueError('fixed native identity/language/index required')
    types=['constructed']+[('NoneType' if language=='python' else 'undefined') if name=='updatePriority' else ('int' if language=='python' else 'number') for name in args[0][1:]]
    return {'i':index,'result':expected,'result_type':'list' if language=='python' else 'object','args_before':args,'args_after':args,'alias_edges':[],'native_route':'direct-event-manager-v1','native_class':'EventManager','native_receiver_count':1,'native_method_return_types':types,'native_method_snapshots':expected}

def check(pid,args,observed,expected,language):
    projected=projected_record(pid,args,expected,language,observed.get('i',0))
    if 'error' in observed:return 'candidate_error'
    for key in ('result','native_method_snapshots'):
        if not oracle.exact(observed.get(key),projected[key]):return 'wrong_answer' if key=='result' else 'native_interface'
    if not oracle.exact(observed.get('args_before'),args) or not oracle.exact(observed.get('args_after'),args) or not oracle.exact(observed.get('alias_edges'),[]):return 'effects'
    for key in ('native_route','native_class','native_receiver_count','result_type','native_method_return_types'):
        if not oracle.exact(observed.get(key),projected[key]):return 'native_interface'
    return None
