"""Independent small-domain controls for three resource-efficient successors."""
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import sys
import time
import qualify as q
from algsolve.judge import sandbox, pinned_runtime


def cases():
    result={1015:[],1079:[],1088:[]}
    for divisor in range(1,1001):
        value=0;answer=-1
        for length in range(1,divisor+1):
            value=value*10+1
            if value%divisor==0:answer=length;break
        result[1015].append({'args':[divisor],'expected':answer})
    for length in range(1,8):
        for a in range(length+1):
            for b in range(length-a+1):
                text='A'*a+'B'*b+'C'*(length-a-b)
                strings=set()
                for size in range(1,len(text)+1):
                    strings.update(itertools.permutations(text,size))
                result[1079].append({'args':[text],'expected':len(strings)})
    rotations={'0':'0','1':'1','6':'9','8':'8','9':'6'};count=0
    for limit in range(1001):
        text=str(limit)
        if limit>0 and all(digit in rotations for digit in text):
            count+=int(''.join(rotations[digit] for digit in reversed(text)))!=limit
        result[1088].append({'args':[limit],'expected':count})
    return result


def run(output,node):
    output.mkdir(parents=True,exist_ok=False);started=time.monotonic();inputs=cases()
    runtime=pinned_runtime.freeze_runtime(node)
    sources={(pid,language):(q.HERE/language/f'{pid:04}.{extension}').read_bytes() for pid in inputs for language,extension in [('python','py'),('javascript','js')]}
    contract={'schema':'gamma.fast-successor-controls.v1','runtime':runtime,'code_sha256':q.sha(Path(__file__).read_bytes()),'runner_sha256':q.sha((q.HERE/'qualify.py').read_bytes()),'sources':{f'{pid}-{lang}':q.sha(raw)for(pid,lang),raw in sources.items()},'cases_sha256':q.sha(q.encoded(inputs)),'batch_size':128,'max_wall_seconds':180,'protected_access':False,'expected_outputs_in_sandbox':False}
    (output/'contract.json').write_bytes(q.encoded(contract));report={'status':'running','contract_sha256':q.sha(q.encoded(contract)),'checks':0,'executions':0,'failures':[],'protected_access':False}
    try:
        for pid,values in inputs.items():
            for language in ('python','javascript'):
                method=json.loads((q.HERE/language/f'{pid:04}.semantics.json').read_text())['entry_point'].split('.')[-1]
                for offset in range(0,len(values),128):
                    if time.monotonic()-started>180:raise TimeoutError('control wall budget')
                    batch=values[offset:offset+128];payload=q.encoded({'method':method,'calls':[{'args':c['args']}for c in batch]})
                    files={'program.py'if language=='python'else'program.js':sources[pid,language],'runner.py'if language=='python'else'runner.cjs':q.PYTHON_RUNNER if language=='python'else q.JAVASCRIPT_RUNNER}
                    limits=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=4*1024**2)
                    result=sandbox.run(['/usr/bin/python3','-I','-S','runner.py'],files=files,stdin=payload,limits=limits)if language=='python'else pinned_runtime.run_node(node,manifest=runtime,files=files,stdin=payload,limits=limits)
                    report['executions']+=1;stem=f'{pid}-{language}-{offset}';(output/(stem+'.stdout')).write_bytes(result.stdout);(output/(stem+'.stderr')).write_bytes(result.stderr)
                    if not result.ok:raise RuntimeError('control process failed: '+stem)
                    rows=q.parse(result.stdout,len(batch))
                    for index,(case,record)in enumerate(zip(batch,rows)):
                        valid=not record.get('error') and type(record.get('result'))is int and record['result']==case['expected'] and q.exact(record.get('args_after'),case['args'])
                        report['checks']+=int(valid)
                        if not valid:report['failures'].append({'id':pid,'language':language,'index':offset+index})
        report['status']='passed'if not report['failures']else'failed'
    except Exception as error:report['status']='failed';report['error']=str(error)
    report['elapsed_seconds']=time.monotonic()-started;(output/'report.json').write_bytes(q.encoded(report));return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--node',type=Path,required=True);a=p.parse_args();r=run(a.output,a.node);print(json.dumps(r));raise SystemExit(0 if r['status']=='passed' else 2)
