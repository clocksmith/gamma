"""Independently reconstruct current-source JSON Python eligibility from raw runs."""
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'paired-authoring-v1'))
import baseline_replay as b
paired=b.module('python_paired_observation_rules',LIT/'paired-authoring-v1/qualify.py')

def verify(inputs,reports):
    inventory={r['problem_id']:r for r in json.loads((LIT/'paired-authoring-v1/manifest.json').read_text())['source_inventory'] if r['language']=='python'}
    eligible={};attempted=set();observations={};report_hashes={};source_hashes={};checks=0
    for path in reports:
        raw=path.read_bytes();report=json.loads(raw);cr=(path.parent/'contract.json').read_bytes();c=json.loads(cr)
        if report.get('schema')!='gamma.paired.frozen-case-replay.v1' or report.get('contract_sha256')!=b.sha(cr) or c.get('protected_access') is not False or c.get('denominator')!=300 or c.get('batch_cases')!=32 or c.get('promotion_authority') is not False:raise ValueError('paired report identity/scope invalid')
        if c.get('python_runtime_sha256')!=b.sha(Path('/usr/bin/python3').read_bytes()):raise ValueError('Python runtime differs')
        ids=c['ids'];loaded,_=paired.inputs(inputs,ids)
        source_ids={r['problem_id']:r for r in c['source_identities'] if r['language']=='python'}
        if set(source_ids)!=set(ids):raise ValueError('incomplete source identity population')
        seen=set()
        for row in report['rows']:
            pid=row['id']
            if pid not in loaded or pid in seen:raise ValueError('unexpected/duplicate result id')
            seen.add(pid);attempted.add(pid)
            if pid in eligible:continue
            data=loaded[pid];cases=json.loads(data['cases']);current=inventory[pid]
            source=(LIT/'paired-authoring-v1'/current['path']).read_bytes();sem=(LIT/'paired-authoring-v1'/current['semantics_path']).read_bytes()
            if source_ids[pid]['sha256']!=b.sha(source) or source_ids[pid]['semantics_sha256']!=b.sha(sem):continue
            if c['input_sha256'][str(pid)]!={k:b.sha(data[k]) for k in ('source','cases')}:raise ValueError('paired input digest drift')
            if row.get('cases_total')!=len(cases) or any(row.get('cases_passed',{}).get(k)!=len(cases) for k in ('python','baseline')):continue
            if any(f.get('variant') in ('python','baseline') for f in row.get('failures',[])):continue
            good=True;proof={}
            for offset in range(0,len(cases),32):
                batch=cases[offset:offset+32]
                py=(path.parent/f'{pid}-python-{offset}.stdout').read_bytes();js=(path.parent/f'{pid}-baseline-{offset}.stdout').read_bytes()
                left=paired.parse(py,len(batch));right=paired.parse(js,len(batch))
                good=good and all(paired.matches(case,a) and paired.matches(case,z) and paired.effects_match(a,z) for case,a,z in zip(batch,left,right))
                proof[str(offset)]={'python_sha256':b.sha(py),'predecessor_sha256':b.sha(js)}
            if not good:raise ValueError('claimed Python pass fails independent raw replay')
            eligible[pid]={'source_path':str(LIT/'paired-authoring-v1'/current['path']),'source_sha256':b.sha(source),'semantics_sha256':b.sha(sem),'cases':len(cases),'report_sha256':b.sha(raw)};observations[str(pid)]=proof;checks+=len(cases)
        report_hashes[str(path)]=b.sha(raw)
    return {'schema':'gamma.python.paired-sourcepool.v1','eligible':{str(k):v for k,v in sorted(eligible.items())},'eligible_ids':sorted(eligible),'attempted_ids':sorted(attempted),'checks':checks,'programs':len(eligible),'reports':report_hashes,'observations':observations,'verifier_sha256':b.sha(Path(__file__).read_bytes()),'comparison_sha256':b.sha(Path(paired.__file__).read_bytes()),'source_form':'Solution.method; standalone solve adapter still requires fresh replay','m1_population':500,'m1_qualified':False,'protected_access':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--report',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.resolve().is_relative_to(HERE.parents[3]):raise ValueError('private proof outside repository required')
    result=verify(a.inputs,a.report);b.write(a.output,result);print(json.dumps({k:result[k] for k in ('programs','checks','m1_qualified')}))
