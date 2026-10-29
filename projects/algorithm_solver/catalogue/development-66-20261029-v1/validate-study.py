"""Validate authored extension shape, local provenance, references and DAG ordering."""
from pathlib import Path
import hashlib
import json
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[4]


def validate(base):
    schema=json.loads((ROOT/'projects/problem_catalogue/schema.v1.json').read_text());records={};dependencies={}
    def walk(value,links):
        if isinstance(value,dict):
            if set(value)=={'kind','id','version','path','sha256'}:
                p=ROOT/value['path'];raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==value['sha256'];d=json.loads(raw);assert (d['kind'],d['id'],d['version'])==(value['kind'],value['id'],value['version']);links.append(p.resolve())
            if set(value)=={'repository','revision','path','sha256','selector'}:
                p=ROOT/value['path'];raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==value['sha256']
                if value['selector']:
                    d=json.loads(raw)
                    for part in value['selector'].lstrip('/').split('/'):
                        part=part.replace('~1','/').replace('~0','~');d=d[int(part)] if isinstance(d,list) else d[part]
            for child in value.values():walk(child,links)
        elif isinstance(value,list):
            for child in value:walk(child,links)
    paths=list((base/'study-records').glob('*.json'))
    expected=json.loads((base/'study-manifest.json').read_text())['records'];assert len(paths)==expected
    for p in paths:
        value=json.loads(p.read_text());assert value['kind'] not in ('evidence','admission');key=(value['kind'],value['id']);assert key not in records;records[key]=value
        definition=value['kind'].title().replace('-','');Draft202012Validator({**schema,'oneOf':[{'$ref':'#/$defs/'+definition}]}).validate(value)
        links=[];walk(value,links);dependencies[p.resolve()]=links
    active=set();done=set()
    def visit(path):
        assert path not in active,'Cyclic study dependencies'
        if path in done:return
        active.add(path)
        for target in dependencies[path]:visit(target)
        active.remove(path);done.add(path)
    for path in dependencies:visit(path)
    print(base.name,'validated',len(paths),'records and their dependency graph')
