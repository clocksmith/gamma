"""Host raw replay; no candidate is imported or executed."""
import argparse,json
from pathlib import Path
from qualify import artifacts,batches,encoded,load_cases,sha,verdict,write,summary,report_for
import oracles as o

def verify(freeze,statements,output):
 raw=freeze.read_bytes();contract=json.loads(raw);assert artifacts(contract['repair_run'])==contract['artifact_hashes'];data=load_cases(statements);assert sha(encoded(data))==contract['cases_sha256'];identity=json.loads((output/'run-identity.json').read_bytes());assert identity['freeze_sha256']==sha(raw)and identity['artifact_hashes']==contract['artifact_hashes']
 sources={(r['problem_id'],r['language']):r for r in contract['source_rows']};summaries=[];batch_count=0
 for pid in o.IDS:
  values=data.get(pid,[])
  if values:assert list(batches(pid,values))==contract['batch_plan'][str(pid)]
  for language in('python','javascript'):
   source=sources[pid,language];failures=[];total=0
   if source['blocked_reason']:failures=[{'gate':'identity_definition_or_adapter','reason':source['blocked_reason']}]
   else:
    for b,indices in enumerate(contract['batch_plan'][str(pid)]):
     stem=f'{pid}-{language}-{b:03d}';start=json.loads((output/(stem+'.start.json')).read_bytes());packet={'entry':'solve','calls':[{'args':values[i]['args']}for i in indices]}
     assert start=={'problem_id':pid,'language':language,'indices':indices,'inputs_sha256':sha(encoded(packet)),'source_sha256':source['sha256']}
     metadata=json.loads((output/(stem+'.result.json')).read_bytes())
     for stream in('stdout','stderr'):assert sha((output/(stem+'.'+stream)).read_bytes())==metadata[stream+'_sha256']
     failures+=verdict(pid,language,values,indices,metadata,(output/(stem+'.stdout')).read_bytes());total+=len(indices);batch_count+=1
   row=summary(source,values,failures,total);assert json.loads((output/f'{pid}-{language}.summary.json').read_bytes())==row;summaries.append(row)
 report=report_for(raw,summaries);assert json.loads((output/'report.json').read_bytes())==report
 hashes={p.name:sha(p.read_bytes())for p in sorted(output.iterdir())if p.is_file()and p.name!='replay.json'}
 return {'schema':'gamma.downloaded-batch08-independent-replay.v1','freeze_sha256':sha(raw),'programs_replayed':len(summaries),'programs_passed':report['programs_passed'],'programs_failed':report['programs_failed'],'programs_blocked':report['programs_blocked'],'programs_execution_failed':report['programs_execution_failed'],'calls_replayed':sum(r['executed_calls']for r in summaries),'sandbox_batches_replayed':batch_count,'case_templates_regenerated':sum(len(v)for v in data.values()),'raw_artifact_hashes':hashes,'all_observations_match_report':True,'canonical_admission_changed':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--freeze',type=Path,required=True);p.add_argument('--statements',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=verify(a.freeze,a.statements,a.output);write(a.output/'replay.json',r);print(json.dumps({k:v for k,v in r.items()if k!='raw_artifact_hashes'}))
