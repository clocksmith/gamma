"""Separately frozen isolated execution/replay of repaired792variants."""
import argparse
from dataclasses import asdict
from pathlib import Path
import json,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import qualify as q
import oracles as o


def cases(statements,baseline):
    values=q.load_cases(statements,baseline['statement_pins'])[792]
    values += [{'args':['a'*50000,['a'*50]*5000],'expected':5000,'category':'maximum-all-words-match'},
               {'args':['ab',['a','a','ab','bb']],'expected':3,'category':'duplicate-multiplicity-control'}]
    return values


def freeze(a):
    baseline=json.loads(a.baseline.read_bytes());values=cases(a.statements,baseline)
    if q.artifacts()!=baseline['artifact_hashes']:raise ValueError('baseline helper drift')
    contract={'schema':'gamma.downloaded-batch06-repair792.v1','baseline_freeze_sha256':q.sha(a.baseline.read_bytes()),
      'baseline_report_sha256':q.sha(a.baseline_report.read_bytes()),'baseline_artifact_hashes':q.artifacts(),
      'runtime':q.runtime(),'helper_sha256':q.sha(Path(__file__).read_bytes()),'case_sha256':q.sha(q.encoded(values)),
      'case_count':len(values),'batch_plan':list(q.batches(values)),'limits':asdict(q.LIMITS),'argv':q.ARGV,
      'sources':{language:{'relative_path':str((HERE/('792.'+ext)).relative_to(q.ROOT)),
                 'sha256':q.sha((HERE/('792.'+ext)).read_bytes())}for language,ext in [('python','py'),('javascript','js')]},
      'scope':'New source identities; functional solve only. Original failures preserved; no catalogue admission or wrapper execution qualification.'}
    q.write(a.contract,contract);print('REPAIR_FROZEN',q.sha(a.contract.read_bytes()),flush=True)


def read(a):
    raw=a.contract.read_bytes();contract=json.loads(raw);baseline=json.loads(a.baseline.read_bytes());values=cases(a.statements,baseline)
    assert q.sha(a.baseline.read_bytes())==contract['baseline_freeze_sha256']
    assert q.artifacts()==contract['baseline_artifact_hashes']
    assert q.sha(Path(__file__).read_bytes())==contract['helper_sha256']
    assert q.sha(q.encoded(values))==contract['case_sha256']
    assert list(q.batches(values))==contract['batch_plan'] and asdict(q.LIMITS)==contract['limits'] and q.ARGV==contract['argv']
    for row in contract['sources'].values():assert q.sha((q.ROOT/row['relative_path']).read_bytes())==row['sha256']
    return raw,contract,values


def execute(a):
    raw,contract,values=read(a);assert q.sha(raw)==a.contract_sha256
    assert q.runtime()==contract['runtime'];a.output.mkdir(parents=True,exist_ok=False)
    q.write(a.output/'identity.json',{'contract_sha256':q.sha(raw),'sources':contract['sources']})
    reports=[]
    for language,extension,harness in [('python','py','harness.py'),('javascript','js','harness.cjs')]:
        failures=[];calls=0
        for i,indices in enumerate(contract['batch_plan']):
            stem=f'{language}-{i:03d}';packet={'entry':'solve','calls':[{'args':values[j]['args']}for j in indices]}
            q.write(a.output/(stem+'.start.json'),{'indices':indices,'inputs_sha256':q.sha(q.encoded(packet))})
            result=q.sandbox.run(q.ARGV[language],files={'program.'+extension:(q.ROOT/contract['sources'][language]['relative_path']).read_bytes(),harness:(q.ROOT/q.TRANSPORT/harness).read_bytes(),'inputs.json':q.encoded(packet)},limits=q.LIMITS)
            metadata=asdict(result)
            for stream in ('stdout','stderr'):
                data=metadata.pop(stream);(a.output/(stem+'.'+stream)).write_bytes(data);metadata[stream+'_sha256']=q.sha(data)
            q.write(a.output/(stem+'.result.json'),metadata)
            failures+=q.verdict(792,language,values,indices,metadata,result.stdout);calls+=len(indices)
        row={'language':language,'source_sha256':contract['sources'][language]['sha256'],'cases':len(values),'calls':calls,'failures':failures,'passed':not failures}
        reports.append(row);print(json.dumps(row),flush=True)
    q.write(a.output/'report.json',{'contract_sha256':q.sha(raw),'programs':reports,'passed':all(r['passed']for r in reports),'canonical_admission_changed':False})


def verify(a):
    raw,contract,values=read(a);assert json.loads((a.output/'identity.json').read_bytes())=={'contract_sha256':q.sha(raw),'sources':contract['sources']}
    reports=[];calls=0
    for language in ('python','javascript'):
        failures=[];count=0
        for i,indices in enumerate(contract['batch_plan']):
            stem=f'{language}-{i:03d}';packet={'entry':'solve','calls':[{'args':values[j]['args']}for j in indices]}
            assert json.loads((a.output/(stem+'.start.json')).read_bytes())=={'indices':indices,'inputs_sha256':q.sha(q.encoded(packet))}
            metadata=json.loads((a.output/(stem+'.result.json')).read_bytes())
            for stream in ('stdout','stderr'):assert q.sha((a.output/(stem+'.'+stream)).read_bytes())==metadata[stream+'_sha256']
            failures+=q.verdict(792,language,values,indices,metadata,(a.output/(stem+'.stdout')).read_bytes());count+=len(indices)
        reports.append({'language':language,'source_sha256':contract['sources'][language]['sha256'],'cases':len(values),'calls':count,'failures':failures,'passed':not failures});calls+=count
    expected={'contract_sha256':q.sha(raw),'programs':reports,'passed':all(r['passed']for r in reports),'canonical_admission_changed':False}
    assert json.loads((a.output/'report.json').read_bytes())==expected
    result={'schema':'gamma.downloaded-batch06-repair792-replay.v1','contract_sha256':q.sha(raw),'calls_replayed':calls,'programs_passed':sum(r['passed']for r in reports),'source_byte_hashes':contract['sources'],'raw_artifact_hashes':{p.name:q.sha(p.read_bytes())for p in sorted(a.output.iterdir())if p.is_file()and p.name!='replay.json'}}
    q.write(a.output/'replay.json',result);print(json.dumps({k:v for k,v in result.items()if k!='raw_artifact_hashes'}),flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=('freeze','run','verify'))
    for name in ('statements','baseline','contract'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--baseline-report',type=Path);parser.add_argument('--output',type=Path);parser.add_argument('--contract-sha256');a=parser.parse_args()
    {'freeze':freeze,'run':execute,'verify':verify}[a.operation](a)
if __name__=='__main__':main()
