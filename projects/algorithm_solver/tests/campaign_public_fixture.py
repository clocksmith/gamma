"""Synthetic metadata/transcript fixtures; never executes candidate code.

No private packet, corpus test data or real review/approval is used here.
"""
from pathlib import Path
import json
from algsolve import campaign_public_contracts as p
from algsolve import corpus_campaign as c
from algsolve import validate
from algsolve.judge import judge,sandbox

def write(path,x):path.write_text(x if isinstance(x,str) else json.dumps(x,indent=2)+'\n');return path

def fixture(root):
    work=root/'qualification';work.mkdir();(work/'normalized').mkdir();(work/'original').mkdir()
    source=write(work/'normalized/0599.py','class Solution:\n    def solve(self, left, right):\n        return left.copy()\n')
    original=write(work/'original/0599.py','class Solution:\n    def solve(self, left, right):\n        return list(left)\n')
    standard=write(work/'policy.json',{'fixture_only':True})
    raw=[{'args':[['oak'],['oak']],'expected':['oak'],'compare':'return'}, {'args':[['pine'],['pine']],'expected':['pine'],'compare':'return'}, {'args':[['alpha','beta'],['beta','alpha']],'expected':['beta','alpha'],'compare':'return'}]
    independent=[{'args':[[f'text{i}'],[f'text{i}']],'expected':[f'text{i}'],'compare':'return'} for i in range(93)]
    sets=[{'uid':'fixture:599','tests':93,'sha256':p.digest(independent),'path':'synthetic-not-loaded.json'}]
    packet={'id':599,'key':'fixture:public-order','statement':'Return the answer in any order.','entry':{'class':'Solution','method':'solve'},'params':[['left','List[str]'],['right','List[str]']],'public_tests':raw,'independent_test_sets':sets}
    pp=write(work/'0599-packet.json',packet);source_sha=c.file_ref(source)['sha256']
    entry={'id':599,'key':packet['key'],'family':'fixture-public-order','language':'python','source':dict(c.file_ref(original),kind='file'),'baseline':{'qualified':True},'independent_sets':sets,'reservation':None,'status':'pending','normalized':None,'claim':None,'attempts':[],'receipts':[],'blockers':[],'revision':0}
    runtime={name:p.sha(path) for name,path in p.RUNTIME.items()}
    registry={'schema':'algsolve.public-comparison-policy.v1','approved_by':'TEST-FIXTURE-coordinator','entries':{entry['key']:{'mode':p.MODE,'packet':c.file_ref(pp),'runtime':runtime}}}
    policy=write(root/'coordinator-policy.json',registry)
    data={'schema':c.SCHEMA,'revision':0,'inputs':{'public_comparison_policy':c.file_ref(policy)},'entries':{'0599:python':entry},'events':[]}
    bound=[dict(t,compare='return:unordered_outer') for t in raw]
    descriptor={'mode':p.MODE,'policy_sha256':c.file_ref(policy)['sha256'],'packet_sha256':c.file_ref(pp)['sha256'],'statement_sha256':p.hashlib.sha256(packet['statement'].encode()).hexdigest(),'raw_public_sha256':p.digest(raw),'bound_public_sha256':p.digest(bound),'runtime':runtime}
    contract={'schema':'algsolve.campaign-contract.v2','entry':'0599:python','source_author':'/root/review_standard','source_sha256':entry['source']['sha256'],'normalized_sha256':source_sha,'independent_sets':sets,'comparison':p.MODE,'independent_comparison':'unchanged','interface':'exact-public-adapter','public_tests':3,'mutation_contract':'Inputs unchanged','alias_contract':'Fresh output list','public_comparison':descriptor}
    cp=write(root/'contract.json',contract);token=c.claim(data,'0599:python','worker')['token']
    historical=write(work/'historical-strict.json',{'fixture_only':True,'public_passed':2,'public_total':3,'independent_passed':93,'independent_total':93})
    write(work/'strict-predecessor.json',{'schema':'algsolve.strict-predecessor.v1','files':[c.file_ref(historical)]})
    freeze={'schema':'algsolve.public-semantic-qualification-freeze.v1','problem_key':entry['key'],'frozen_before_new_execution_and_independent_reload':True,'packet_sha256':descriptor['packet_sha256'],'statement_sha256':descriptor['statement_sha256'],'raw_public_sha256':descriptor['raw_public_sha256'],'bound_public_sha256':descriptor['bound_public_sha256'],'independent_comparison':'unchanged','independent_sets':sets,'limits':{'cpu_seconds':3,'wall_seconds':8,'memory_bytes':1024**3,'serial_cpus':1,'max_output_bytes':4*1024**2},'runtime':[{'path':str(path),'sha256':runtime[name]} for name,path in p.RUNTIME.items()],'files':{str(path.relative_to(work)):p.sha(path) for path in work.rglob('*') if path.is_file()}}
    write(work/'freeze.json',freeze)
    groups=[{'name':'public','raw_tests':raw,'effective_tests':bound},{'name':'independent:fixture:599','raw_tests':independent,'effective_tests':independent}];write(work/'host-only-tests.json',groups)
    chunks=[]
    for group in groups:
        for offset in range(0,len(group['raw_tests']),16):
            cases=group['raw_tests'][offset:offset+16];effective=group['effective_tests'][offset:offset+16]
            rows=[{'i':i,'args_before':t['args'],'args_after':t['args'],'input_node_values_preserved':True,'returned_input_ids':[],'result':t['args'][0]} for i,t in enumerate(cases)]+[{'done':len(cases)}]
            payload={'exit_code':0,'signal':None,'stdout':'\n'.join(json.dumps(x) for x in rows)+'\n','stderr':'','wall_seconds':0.01,'timed_out':False,'output_limit_exceeded':False,'notes':['SYNTHETIC UNIT-TEST TRANSCRIPT; NOT AN EXECUTION RECEIPT']}
            result=sandbox.SandboxResult(**dict(payload,stdout=payload['stdout'].encode(),stderr=b''))
            chunks.append({'group':group['name'],'offset':offset,'count':len(cases),'raw_cases_sha256':p.digest(cases),'effective_cases_sha256':p.digest(effective),'result':payload,'verdict':judge._score_functional(result,validate.functional_tests(effective)).to_dict(),'strict_verdict':judge._score_functional(result,validate.functional_tests(cases)).to_dict(),'mutation_alias_ok':True})
    q={'schema':'algsolve.public-semantic-qualification.v1','source_author':contract['source_author'],'problem_key':entry['key'],'freeze_sha256':p.sha(work/'freeze.json'),'host_tests_sha256':p.sha(work/'host-only-tests.json'),'packet_sha256':descriptor['packet_sha256'],'raw_public_sha256':descriptor['raw_public_sha256'],'bound_public_sha256':descriptor['bound_public_sha256'],'public_comparison':'statement-declared:unordered_outer.v1','independent_comparison':'unchanged','independent_sets':sets,'candidate_bytes_changed':False,'expected_outputs_changed':False,'expected_values_in_sandbox':False,'results':[{'variant':'original','language':'python','source_sha256':p.sha(original),'chunks':chunks},{'variant':'normalized','language':'python','source_sha256':source_sha,'chunks':chunks}]}
    write(work/'qualification.json',q)
    return {'root':root,'work':work,'entry':entry,'data':data,'contract':contract,'contract_path':cp,'source':source,'standard':standard,'token':token,'policy':policy}

def stage(f):return c.stage(f['data'],'0599:python','worker',f['token'],f['source'],f['contract_path'],f['standard'],f['root'])
def evidence(f):
    a=f['entry']['attempts'][-1];work=f['work'];contract=f['contract'];descriptor=contract['public_comparison']
    qref=c.file_ref(work/'qualification.json');fref=c.file_ref(work/'freeze.json');href=c.file_ref(work/'host-only-tests.json');pref=c.file_ref(work/'strict-predecessor.json')
    _,_,_,refs=p.profile(f['data'],f['entry'],contract)
    freeze=json.loads((work/'freeze.json').read_text());predecessor=json.loads((work/'strict-predecessor.json').read_text())
    refs += [qref,fref,href,pref]+predecessor['files']+freeze['runtime']+[c.file_ref(work/rel) for rel in freeze['files']]
    common={'schema':'algsolve.campaign-evidence.v1','entry':'0599:python','source_sha256':a['source_sha256'],'normalized_sha256':a['normalized']['sha256'],'contract_sha256':a['contract']['sha256'],'status':'passed','artifacts':refs}
    return {'standard':dict(common,kind='standard',standard_sha256=a['standard']['sha256'],errors=[],idempotent=True),'execution':dict(common,kind='execution',independent_sets=f['entry']['independent_sets'],independent_total=93,independent_passed=93,public_total=3,public_passed=3,strict_public_passed=2,mutation_passed=True,alias_passed=True,sandboxed=True,infrastructure_errors=0,expected_outputs_in_sandbox=False,public_comparison=descriptor,independent_comparison='unchanged',semantic_qualification=qref,qualification_freeze=fref,host_tests=href,strict_predecessor=pref),'review':dict(common,kind='review',reviewer='TEST-FIXTURE-independent-reviewer',semantic_role_mapping_reviewed=True,complexity_reviewed=True,unresolved=[],public_comparison_reviewed=True,public_comparison_sha256=p.digest(descriptor))}
def bundle(f,receipts):return write(f['root']/'bundle.json',{kind:c.file_ref(write(f['root']/(kind+'.json'),value)) for kind,value in receipts.items()})
def record(f,receipts):c.record(f['data'],'0599:python','worker',f['token'],bundle(f,receipts),f['root'])
