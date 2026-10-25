"""Input-only local worker: expected outputs are never passed to this process."""
import copy
import json
from pathlib import Path
import runpy
import sys
import time

root=Path(__file__).resolve().parents[1]
pid=int(sys.argv[1])
assignment=json.loads((root/'assignment.json').read_text())
problem=next(p for p in assignment['problems'] if p['id']==pid)
namespace=runpy.run_path(str(root/'python'/f'{pid:04}.py'))
instance=namespace['Solution']()
functions={'solve':namespace['solve'],'native':getattr(instance,problem['native'])}


def containers(value):
    result=[]
    if isinstance(value,list):
        result.append(value)
        for item in value:
            result.extend(containers(item))
    return result


for line in sys.stdin:
    request=json.loads(line)
    results={}
    for name,function in functions.items():
        args=copy.deepcopy(request['args'])
        before=copy.deepcopy(args)
        references=containers(args)
        start=time.perf_counter_ns()
        try:
            output=function(*args)
            after_references=containers(args)
            alias_changed=(len(references)!=len(after_references) or
                           any(a is not b for a,b in zip(references,after_references)))
            results[name]={'ok':True,'value':output,'type':type(output).__name__,
                'input_changed':args!=before,'container_identity_changed':alias_changed,
                'elapsed_ns':time.perf_counter_ns()-start}
        except Exception as error:
            results[name]={'ok':False,'error':type(error).__name__+': '+str(error),
                           'elapsed_ns':time.perf_counter_ns()-start}
    print(json.dumps({'case_id':request['case_id'],'results':results},separators=(',',':'),allow_nan=False))
