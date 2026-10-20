import hashlib,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from algsolve.literal_editor import ROOT,PROFILE,DICTIONARY_SHA,check
start=time.perf_counter();m=json.loads((ROOT/'pass2/working/packages/shared7/manifest.json').read_text());rows=[]
for key,row in sorted(m['programs'].items()):
 bits=''.join(f'{i:07b}' for i in row['sequence'])+'1111111'
 result=check({'operation':'literal_check','profile':PROFILE,'dictionary_sha256':DICTIONARY_SHA,'problem_id':key,'bits':bits})
 assert result['passed'] and result['source_sha256']==row['source_sha256'],result
 result['bits_sha256']=hashlib.sha256(bits.encode()).hexdigest();rows.append(result)
 print(key,result['tests_passed'],flush=True)
negative=check({'operation':'literal_check','profile':PROFILE,'dictionary_sha256':DICTIONARY_SHA,'problem_id':'0242','bits':'00000001111111'})
assert not negative['passed'] and negative['reason']=='sandbox_failure'
result={'schema':'gamma.literal-editor-qualification.v1','dictionary_sha256':DICTIONARY_SHA,'profile':PROFILE,'programs':len(rows),'checks_passed':sum(r['tests_passed'] for r in rows),'checks_total':sum(r['tests_total'] for r in rows),'rows':rows,'invalid_source_rejected':negative,'seconds':time.perf_counter()-start,'runtime_sha256':hashlib.sha256((Path(__file__).resolve().parents[2]/'algsolve/literal_editor.py').read_bytes()).hexdigest(),'scope':'Actual isolated known-development checks through literal_check; no autonomous synthesis or protected evaluation.'}
Path(sys.argv[1]).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['programs','checks_passed','checks_total','seconds']}))
