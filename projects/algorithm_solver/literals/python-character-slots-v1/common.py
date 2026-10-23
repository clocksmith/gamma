"""Pure adapters; importing this module never opens population files."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import sys

HERE=Path(__file__).resolve().parent; LIT=HERE.parent
sys.path.insert(0,str(LIT/'cost-decomposition-v1'))
import analyze

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

repair=module('python_slots_actual_flow',LIT/'character-slots-v1/repair.py')
tail=module('python_slots_costs',LIT/'tail-search-v1/search.py')
ALPHABET=repair.ALPHABET
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def require_assertions():
    if not __debug__ or sys.flags.optimize or 'PYTHONOPTIMIZE' in os.environ:
        raise RuntimeError('Optimized Python/PYTHONOPTIMIZE forbidden: evidence checks require assertions')

def enforce_limits(c):
    require_assertions()
    maximum=c['limits']['address_space_bytes']
    resource.setrlimit(resource.RLIMIT_AS,(maximum,maximum))

def write(path,obj):
    path=Path(path);tmp=path.with_name(path.name+'.tmp')
    with tmp.open('w') as f:
        json.dump(obj,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)

def checked(spec):
    raw=Path(spec['file']).read_bytes();assert sha(raw)==spec['sha256'],spec['file'];return json.loads(raw)

def ordered(vocab):
    return [s for s in ALPHABET if s in vocab]+sorted(s for s in set(vocab) if len(s)>1)

def banned(texts,entries):
    """Python Solution entry method/body, full source; no JavaScript solve probe."""
    result=set(texts.values())
    for pid,text in texts.items():
        tree=ast.parse(text);lines=re.findall(r'.*?(?:\r\n|\r|\n|$)',text)
        if lines and not lines[-1]:lines.pop()
        found=False
        for cls in tree.body:
            if not isinstance(cls,ast.ClassDef) or cls.name!='Solution':continue
            for node in cls.body:
                if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) or node.name!=entries[str(pid)]:continue
                found=True
                result.add(ast.get_source_segment(text,node))
                result.add(''.join(lines[node.lineno-1:node.end_lineno]).rstrip('\r\n'))
                first,last=node.body[0],node.body[-1]
                chunk=''.join(lines[first.lineno-1:last.end_lineno])
                result.add(chunk.rstrip('\r\n'))
                result.add(chunk.encode()[first.col_offset:].decode().rstrip('\r\n'))
                body=''.join(lines[first.lineno-1:last.end_lineno-1]).encode()+lines[last.end_lineno-1].encode()[:last.end_col_offset]
                result.add(body[first.col_offset:].decode())
        assert found,('missing Python entry',pid)
    return {x for x in result if x}

def authority(c,width,arm,texts):
    proof=checked(c['qualification'])
    a=next(x for x in proof['arms'] if x['width']==width and x['arm']==arm)
    for pid,text in texts.items():
        assert a['qualification'][str(pid)]['passed'],('unqualified',pid)
        assert a['per_problem'][str(pid)]['source_sha256']==sha(text.encode()),('source mismatch',pid)
    return a

def evaluate(texts,vocab,width,c):
    assert vocab==ordered(vocab) and len(vocab)==len(set(vocab))<=2**width
    rows,illegal=tail.evaluate_output(texts,vocab,width,banned(texts,c['entries']))
    db=analyze.dictionary_bytes(vocab)
    return {'width':width,'entries':len(vocab),'character_entries':sum(len(s)==1 for s in vocab),
            'dictionary_bytes':len(db),'dictionary_binary_sha256':sha(db),'per_problem':rows,
            'illegal_entry_sha256':illegal,'qualified':len(texts),
            'fit':tail.aggregate(rows,c['partition']['dev_fit'],len(db)),
            'validation':tail.aggregate(rows,c['partition']['dev_val'],len(db))}
