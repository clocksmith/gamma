"""Capture raw observations while executing the unchanged strict parity procedure."""
from dataclasses import asdict
import json
from pathlib import Path
import core as c


def execute(work,pid,source,spec,folder):
    minify=c.module('atomic_raw_minify',c.LIT/'minify-control-v1/minify.py')
    from algsolve.judge import sandbox
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
    receipt={'pid':str(pid),'source_sha256':c.sha(source.encode()),'entry':'solve','complete':False,'batches':[]}
    c.write(folder/'receipt.json',receipt)
    actual=sandbox.run;offset=0
    def capture(argv,*,files,stdin=b'',limits=sandbox.Limits()):
        nonlocal offset
        inputs=json.loads(files['inputs.json']);assert files['program.js']==source and inputs['entry']=='solve'
        count=len(inputs['calls']);number=len(receipt['batches'])
        row={'offset':offset,'count':count,'argv':argv,'limits':asdict(limits),
             'stdin_sha256':c.sha(stdin),'input_files':{name:c.sha(value.encode() if isinstance(value,str) else value) for name,value in files.items()},
             'complete':False}
        receipt['batches'].append(row);c.write(folder/'receipt.json',receipt)
        try:res=actual(argv,files=files,stdin=stdin,limits=limits)
        except BaseException as error:
            row.update(error_type=type(error).__name__,error=str(error));c.write(folder/'receipt.json',receipt);raise
        stdout=f'{number}.stdout';stderr=f'{number}.stderr'
        (folder/stdout).write_bytes(res.stdout);(folder/stderr).write_bytes(res.stderr)
        row.update(complete=True,stdout=stdout,stderr=stderr,stdout_sha256=c.sha(res.stdout),stderr_sha256=c.sha(res.stderr),
                   exit_code=res.exit_code,signal=res.signal,timed_out=res.timed_out,output_limit_exceeded=res.output_limit_exceeded,
                   wall_seconds=res.wall_seconds,notes=res.notes,ok=res.ok)
        offset+=count;c.write(folder/'receipt.json',receipt)
        return res
    sandbox.run=capture
    try:
        passed,ok,total,bad=minify.style.parity(minify.shim(Path(work)),pid,source,'solve',spec,None)
        receipt.update(complete=True,passed=bool(passed),checks_passed=ok,cases=total,mismatches=bad)
        c.write(folder/'receipt.json',receipt)
        return passed,ok,total,bad,c.sha((folder/'receipt.json').read_bytes())
    except BaseException as error:
        receipt.update(error_type=type(error).__name__,error=str(error));c.write(folder/'receipt.json',receipt);raise
    finally:sandbox.run=actual
