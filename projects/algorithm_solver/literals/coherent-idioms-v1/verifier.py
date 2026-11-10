"""Independent finite integer-envelope verifier, never a source-program judge.

Only two distinct ASCII local variable names and +=/-= are executable here.
No calls, indexing, attributes, literals, object coercion or source bodies run.
"""
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess


def verify_accumulator(literal, language):
    if language not in ('python','javascript'): raise ValueError('unsupported language')
    pattern = r'([A-Za-z_][A-Za-z_0-9]*)\s*([+-])=\s*([A-Za-z_][A-Za-z_0-9]*)'
    m = re.fullmatch(pattern + (r';?' if language=='javascript' else ''), literal.strip())
    if not m or m[1] == m[3] or any(x.startswith('__') for x in (m[1],m[3])): return None
    left,op,right=m.groups()
    if left == 'sentinel' or right == 'sentinel': return None
    inputs = [(a,b) for a in range(-8,9) for b in range(-8,9)]
    # Oracle is signed repeated unit movement, separate from the candidate operator.
    expected=[]
    for a,b in inputs:
        value=a
        direction=(1 if b>=0 else -1)*(1 if op=='+' else -1)
        for _ in range(abs(b)): value += direction
        expected.append([value,b,917])
    try:
        if language=='python':
            code=compile(literal.strip(),'<local-primitive>','exec'); actual=[]
            for a,b in inputs:
                env={left:a,right:b,'sentinel':917}
                exec(code,{'__builtins__':{}},env)
                actual.append([env[left],env[right],env['sentinel']])
            runtime=platform.python_version()
        else:
            body = literal + '; return ['+left+','+right+'];'
            script = ('"use strict"; const inputs='+json.dumps(inputs)+
                '; const f=new Function('+json.dumps(left)+','+json.dumps(right)+','+json.dumps(body)+
                '); const actual=inputs.map(pair=>[...f(...pair),917]); console.log(JSON.stringify({runtime:process.version,actual}));')
            p=subprocess.run(['node','-e',script],capture_output=True,text=True,timeout=10,check=True)
            result=json.loads(p.stdout); actual=result['actual']; runtime=result['runtime']
    except (SyntaxError,ValueError,subprocess.SubprocessError):
        return {'passed':False,'scope':'local-primitive-only','reason':'bounded execution failed'}
    return {'passed':actual==expected,'scope':'local-primitive-only',
            'contract':'distinct-local-integer-add-subtract-v1',
            'preconditions':{'left_integer_range':[-8,8],'right_integer_range':[-8,8],
                'distinct_local_names':[left,right],'no_coercion_or_alias_objects':True},
            'postconditions':['left equals mathematical result','right unchanged','sentinel unchanged'],
            'cases':len(inputs),'runtime':runtime,'language':language,
            'literal_sha256':hashlib.sha256(literal.encode()).hexdigest(),
            'verifier_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'cases_sha256':hashlib.sha256(json.dumps(inputs).encode()).hexdigest(),
            'full_source_qualification':False,'unseen_solving':False}
