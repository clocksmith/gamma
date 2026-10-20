"""Frozen literal input protocol and isolated development checks for the editor.

No source insertion, retrieval, model generation, protected data or new auth policy.
"""
import hashlib, importlib.util, json, re, sys
from pathlib import Path
from .judge import sandbox
ROOT=Path(__file__).resolve().parents[1]/'literals'
PROFILE='gamma.literal-shared7-interactive.v1'
DICTIONARY_SHA='62ab89348d4781187375f35663f81b6304a70b9f951d9bd3327fecae6d3b8c39'
CHECKS_SHA='f008e7dc7c643b81ccc5b6f74df63a1f8fce8a52a8b6d32fc67a7d2a13a81df9'
MAX_BITS=8190

def sha(raw):return hashlib.sha256(raw).hexdigest()
def load_language():
    folder=ROOT/'pass2/working/packages/shared7'
    raw=(folder/'dictionary.ltd').read_bytes()
    if sha(raw)!=DICTIONARY_SHA:raise ValueError('Frozen dictionary drift')
    pos=8;values=[]
    if raw[:4]!=b'LTD1' or int.from_bytes(raw[4:8],'big')!=79:raise ValueError('Dictionary format')
    for _ in range(79):
        n=int.from_bytes(raw[pos:pos+4],'big');pos+=4
        values.append(raw[pos:pos+n].decode('utf-8'));pos+=n
    if pos!=len(raw):raise ValueError('Dictionary length')
    return values

def decode(bits):
    if not isinstance(bits,str) or len(bits)>MAX_BITS or re.fullmatch('[01]*',bits) is None:raise ValueError('Invalid or oversized bitstream')
    if len(bits)%7:raise ValueError('Incomplete seven-bit word')
    values=load_language();selected=[];finished=False;literal_bits=control_bits=0
    for offset in range(0,len(bits),7):
        if finished:raise ValueError('Bits after Finish')
        item=int(bits[offset:offset+7],2)
        if item<79:
            selected.append(item);literal_bits+=7
            if len(''.join(values[i] for i in selected).encode())>65536:raise ValueError('Assembled source exceeds 64 KiB')
        elif item==125:control_bits+=7;selected=selected[:-1]
        elif item==126:control_bits+=7;selected=[]
        elif item==127:
            control_bits+=7
            if not selected:raise ValueError('Cannot finish an empty program')
            finished=True
        else:raise ValueError(f'Unused literal ID {item}')
    if not finished:raise ValueError('Finish code required')
    source=''.join(values[i] for i in selected)
    return {'source':source,'selections':selected,'source_sha256':sha(source.encode()),'cost':{'literal_bits':literal_bits,'control_bits':control_bits,'total_bits':len(bits),'source_only_bits':len(selected)*7}}

def _module(name,path,raw):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    exec(compile(raw,str(path),'exec'),module.__dict__);return module

def check(payload):
    if set(payload)!={'operation','profile','dictionary_sha256','problem_id','bits'} or payload['operation']!='literal_check' or payload['profile']!=PROFILE or payload['dictionary_sha256']!=DICTIONARY_SHA:raise ValueError('Literal request identity/fields mismatch')
    manifest=json.loads((ROOT/'pass2/working/packages/shared7/manifest.json').read_bytes());key=payload['problem_id']
    if not isinstance(key,str) or key not in manifest['programs']:raise ValueError('Unknown literal problem')
    decoded=decode(payload['bits']);raw=(ROOT/'checks.py').read_bytes()
    if sha(raw)!=CHECKS_SHA:raise ValueError('Development checks drift')
    checks=_module('literal_editor_checks',ROOT/'checks.py',raw)
    # Reuse the same bounded source-only harness as the frozen development run.
    sys.path.insert(0,str(ROOT))
    try:
        from verify_execution import HARNESS,strict_object
    finally:sys.path.remove(str(ROOT))
    cases=checks.cases_by_problem[int(key)];passed=0;failures=[];calls=0
    for offset in range(0,len(cases),256):
        selected=cases[offset:offset+256]
        data=json.dumps({'interface':'function','calls':[{'args':c['args']} for c in selected]},ensure_ascii=False).encode()
        result=sandbox.run(['/usr/bin/node','--jitless','--single-threaded','--max-old-space-size=64','harness.cjs'],files={'program.js':decoded['source'],'inputs.json':data,'harness.cjs':HARNESS},limits=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=4*1024**2));calls+=1
        if not result.ok:
            return {'passed':False,'reason':'sandbox_failure','tests_passed':passed,'tests_total':len(cases),'completed_checks':offset,'source_sha256':decoded['source_sha256'],'dictionary_sha256':DICTIONARY_SHA,'timed_out':result.timed_out,'exit_code':result.exit_code,'cost':decoded['cost'],'problem_id':key}
        records=[json.loads(line,object_pairs_hook=strict_object,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x))) for line in result.stdout.splitlines()]
        if len(records)!=len(selected)+1 or records[-1]!={'done':len(selected)} or type(records[-1].get('done')) is not int:raise ValueError('Output completion protocol')
        for i,record in enumerate(records[:-1]):
            if type(record.get('i')) is not int or record['i']!=i:raise ValueError('Output ordering')
            verdict=checks.check_observation(int(key),offset+i,record);passed+=verdict['passed']
            if not verdict['passed'] and len(failures)<8:failures.append({'case':offset+i,'reason':verdict})
    return {'passed':passed==len(cases),'tests_passed':passed,'tests_total':len(cases),'failures':failures,'source_sha256':decoded['source_sha256'],'dictionary_sha256':DICTIONARY_SHA,'profile':PROFILE,'problem_id':key,'checks_sha256':CHECKS_SHA,'sandbox_calls':calls,'cost':decoded['cost'],'scope':'Known development cases, including input preservation; not autonomous synthesis or held-out qualification.'}
