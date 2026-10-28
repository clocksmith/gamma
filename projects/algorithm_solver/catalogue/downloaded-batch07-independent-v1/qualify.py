"""Hash-frozen sequential isolated judging for the owner-provided batch07."""
import argparse,hashlib,json,os,platform,re,subprocess,sys,traceback
from datetime import datetime,timezone
from dataclasses import asdict
from pathlib import Path
import cases
import oracles as o
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'projects/algorithm_solver'))
from algsolve.judge import sandbox
IMPORT=Path('projects/algorithm_solver/catalogue/authored/downloaded-general50-v1')
TRANSPORT=Path('projects/algorithm_solver/catalogue/public-domain-qualification-easy16-v1')
LIMITS=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=16*1024**2)
ARGV={'python':['/usr/bin/python3','-I','-S','harness.py'],'javascript':['/usr/bin/node','--jitless','--single-threaded','--max-old-space-size=256','harness.cjs']}

def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())

def runtime():
    refs = {}
    for name in ('python3', 'node', 'bwrap', 'prlimit'):
        path = Path('/usr/bin') / name
        refs[str(path)] = sha(path.read_bytes())
        proc = subprocess.run(['/usr/bin/ldd', str(path)], capture_output=True, text=True, check=True)
        for dep in re.findall(r'(?:=>\s*)?(/[^\s()]+)', proc.stdout):
            refs[dep] = sha(Path(dep).read_bytes())
    lib = Path(subprocess.check_output(['/usr/bin/python3', '-I', '-S', '-c',
                'import sysconfig;print(sysconfig.get_path("stdlib"))'], text=True).strip())
    standard = {str(p.relative_to(lib)): sha(p.read_bytes()) for p in sorted(lib.rglob('*'))
                if p.is_file() and p.suffix in ('.py', '.so') and
                'site-packages' not in p.parts and '__pycache__' not in p.parts}
    return {'executables_and_linked_libraries': refs, 'python_stdlib_path': str(lib),
            'python_stdlib_files': standard,
            'python_version': subprocess.check_output(['/usr/bin/python3', '--version'], text=True).strip(),
            'node_version': subprocess.check_output(['/usr/bin/node', '--version'], text=True).strip()}

def parse(raw, count):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate observation key')
            result[key] = value
        return result
    rows = [json.loads(line, object_pairs_hook=pairs,
                       parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
            for line in raw.decode('utf8').splitlines()]
    if (len(rows) != count + 1 or type(rows[-1]) is not dict or set(rows[-1]) != {'done'}
            or type(rows[-1]['done']) is not int or rows[-1]['done'] != count):
        raise ValueError('incomplete observation stream')
    for i, row in enumerate(rows[:-1]):
        if not isinstance(row, dict) or type(row.get('i')) is not int or row['i'] != i:
            raise ValueError('observation order mismatch')
        required = {'i', 'error'} if 'error' in row else {
            'i', 'result', 'result_type', 'args_before', 'args_after', 'alias_edges'}
        if set(row) != required:
            raise ValueError('observation shape mismatch')
    return rows[:-1]

def verdict(pid, language, values, indices, metadata, stdout):
    if not (metadata['exit_code'] == 0 and not metadata['timed_out']
            and not metadata['output_limit_exceeded']):
        return [{'case': i, 'reason': 'sandbox_process_failure'} for i in indices]
    try:
        rows = parse(stdout, len(indices))
    except (ValueError, UnicodeError, TypeError):
        return [{'case': i, 'reason': 'observation_protocol'} for i in indices]
    failures = []
    for index, row in zip(indices, rows):
        case = values[index]
        ok, reason = o.compare(pid, case['args'], case['expected'], row, language)
        if not ok:
            failures.append({'case': index, 'reason': reason})
    return failures


def source_rows(repairs=False):
 manifest=json.loads((ROOT/IMPORT/'manifest.json').read_bytes());rows=manifest['source_inventory'];assert len(rows)==100 and {r['id']for r in rows}==set(o.IDS)
 selected=[]
 replacements={}
 if repairs:
  m=json.loads((HERE/'repairs/manifest.json').read_bytes());replacements={(r['problem_id'],r['language']):r for r in m['repairs']}
 for row in rows:
  key=row['id'],row['language'];path=ROOT/IMPORT/row['path'];expected=row['sha256']
  if key in replacements:path=HERE/replacements[key]['source_path'];expected=replacements[key]['source_sha256']
  assert sha(path.read_bytes())==expected
  selected.append({'problem_id':row['id'],'language':row['language'],'path':str(path.relative_to(ROOT)),'sha256':expected,'original_source_sha256':row['sha256'],'repaired':key in replacements})
 return selected


def artifacts(repairs=False):
 paths=list(HERE.glob('*.py'))+[HERE/'README.md',HERE/'contracts.json',ROOT/IMPORT/'manifest.json',ROOT/IMPORT/'assignment.public-safe.json',ROOT/'projects/algorithm_solver/algsolve/judge/sandbox.py']
 paths += [ROOT/TRANSPORT/p for p in('harness.py','harness.cjs')]
 paths += [ROOT/r['path']for r in source_rows(repairs)]
 if repairs:paths += list((HERE/'repairs').rglob('*.py'))+list((HERE/'repairs').rglob('*.js'))+[HERE/'repairs/manifest.json',HERE/'repairs/independent-review.json']
 return {str(p.relative_to(ROOT)):sha(p.read_bytes())for p in sorted(set(paths))}


def load_cases(statements):
 contracts=json.loads((HERE/'contracts.json').read_bytes());assert set(map(int,contracts['problems']))==set(o.IDS)
 for pid,row in contracts['problems'].items():
  raw=(Path(statements)/(pid+'.json')).read_bytes();q=json.loads(raw)['data']['question'];assert q['questionFrontendId']==pid and sha(raw)==row['statement_snapshot_sha256']and sha(q['content'].encode())==row['statement_content_sha256']
 return cases.build(statements)


def batches(pid,values):
 batch=[];size=0
 for index,case in enumerate(values):
  length=len(encoded(case['args']))
  if batch and (pid==866 or len(batch)>=16 or size+length>128*1024):
   yield batch+([batch[0]]if size<=128*1024 and pid!=866 else[]);batch=[];size=0
  batch.append(index);size+=length
 if batch:yield batch+([batch[0]]if size<=128*1024 and pid!=866 else[])


def memory():
 values={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()if line.startswith(('MemTotal:','MemAvailable:'))}
 if values['MemAvailable']<4*1024**3:raise RuntimeError('insufficient measured host memory for sequential qualification')
 return values


def freeze(args):
 data=load_cases(args.statements);profile=runtime();resources=memory();rows=source_rows(args.repairs)
 preflight=args.preflight.read_bytes();assert b'37 passed'in preflight
 contract={'schema':'gamma.downloaded-batch07-independent-freeze.v1','created_at':datetime.now(timezone.utc).isoformat(),'repair_run':args.repairs,'artifact_hashes':artifacts(args.repairs),'source_rows':rows,'runtime':profile,'argv':ARGV,'limits':asdict(LIMITS),'case_counts':{str(k):len(v)for k,v in data.items()},'cases_sha256':sha(encoded(data)),'batch_plan':{str(k):list(batches(k,v))for k,v in data.items()},'maximum_concurrent_candidate_interpreters':1,'host_memory_observation':resources,'preflight_sha256':sha(preflight),'qualification_scope':'Functional solve adapter; read-only inputs and fresh mutable returns. Official class wrappers are not execution-qualified.','expected_results_enter_sandbox':False,'canonical_promotion':False}
 write(args.freeze,contract);print('FROZEN',sha(args.freeze.read_bytes()),flush=True)


def execute(args):
 raw=args.freeze.read_bytes();assert sha(raw)==args.freeze_sha256;contract=json.loads(raw);repairs=contract['repair_run'];assert artifacts(repairs)==contract['artifact_hashes'];assert runtime()==contract['runtime'];assert contract['argv']==ARGV and contract['limits']==asdict(LIMITS)
 data=load_cases(args.statements);assert sha(encoded(data))==contract['cases_sha256'];mem=memory();args.output.mkdir(parents=True,exist_ok=False)
 write(args.output/'run-identity.json',{'freeze_sha256':sha(raw),'started_at':datetime.now(timezone.utc).isoformat(),'hostname':platform.node(),'artifact_hashes':artifacts(repairs),'host_memory':mem,'maximum_concurrent_candidate_interpreters':1})
 sources={(r['problem_id'],r['language']):r for r in contract['source_rows']};summaries=[]
 for pid in o.IDS:
  values=data[pid];assert list(batches(pid,values))==contract['batch_plan'][str(pid)]
  for language,extension,harness in [('python','py','harness.py'),('javascript','js','harness.cjs')]:
   failures=[];total=0;source=sources[pid,language]
   for b,indices in enumerate(contract['batch_plan'][str(pid)]):
    packet={'entry':'solve','calls':[{'args':values[i]['args']}for i in indices]};stem=f'{pid}-{language}-{b:03d}'
    write(args.output/(stem+'.start.json'),{'problem_id':pid,'language':language,'indices':indices,'inputs_sha256':sha(encoded(packet)),'source_sha256':source['sha256']})
    try:
     result=sandbox.run(ARGV[language],files={'program.'+extension:(ROOT/source['path']).read_bytes(),harness:(ROOT/TRANSPORT/harness).read_bytes(),'inputs.json':encoded(packet)},limits=LIMITS)
    except BaseException as error:
     write(args.output/(stem+'.setup-failure.json'),{'error_type':type(error).__name__,'error':str(error),'traceback':traceback.format_exc()});raise
    metadata=asdict(result)
    for stream in('stdout','stderr'):
     payload=metadata.pop(stream);p=args.output/(stem+'.'+stream)
     with p.open('xb')as f:f.write(payload);f.flush();os.fsync(f.fileno())
     metadata[stream+'_sha256']=sha(payload)
    write(args.output/(stem+'.result.json'),metadata)
    failures += verdict(pid,language,values,indices,metadata,result.stdout);total+=len(indices)
   row={'problem_id':pid,'language':language,'source_sha256':source['sha256'],'source_path':source['path'],'original_source_sha256':source['original_source_sha256'],'repaired':source['repaired'],'distinct_cases':len(values),'executed_calls':total,'failures':failures,'passed':not failures,'official_wrapper_execution_qualified':False}
   summaries.append(row);write(args.output/f'{pid}-{language}.summary.json',row);print(json.dumps({k:v for k,v in row.items()if k!='failures'}),flush=True)
 report={'schema':'gamma.downloaded-batch07-independent-report.v1','freeze_sha256':sha(raw),'programs':summaries,'programs_passed':sum(r['passed']for r in summaries),'programs_failed':sum(not r['passed']for r in summaries),'canonical_admission_changed':False,'scope':contract['qualification_scope']}
 write(args.output/'report.json',report)


def main():
 p=argparse.ArgumentParser();p.add_argument('operation',choices=('freeze','run'));p.add_argument('--statements',type=Path,required=True);p.add_argument('--freeze',type=Path,required=True);p.add_argument('--preflight',type=Path);p.add_argument('--output',type=Path);p.add_argument('--freeze-sha256');p.add_argument('--repairs',action='store_true');a=p.parse_args();(freeze if a.operation=='freeze'else execute)(a)
if __name__=='__main__':main()
