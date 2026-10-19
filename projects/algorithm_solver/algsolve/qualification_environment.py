"""Optional catalog gate for observed judge executable and stdlib identities.

This checks fixed local runtime paths; manifests cannot supply executable paths
or commands. It does not alter or install anything in the execution environment.
"""
import hashlib
import json
from pathlib import Path
import subprocess

EXECUTABLES=('/usr/bin/python3','/usr/bin/bwrap','/usr/bin/prlimit')
SCHEMA='algsolve.judge-environment.v1'


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture():
    info=json.loads(subprocess.check_output([EXECUTABLES[0],'-I','-S','-c',
        'import sys,sysconfig,json;print(json.dumps({"version":sys.version,"stdlib":sysconfig.get_path("stdlib"),"executable":sys.executable}))'],
        text=True,timeout=10))
    root=Path(info['stdlib']);files={}
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.suffix not in ('.py','.so'):continue
        if any(part in path.parts for part in ('site-packages','dist-packages','__pycache__')):continue
        files[str(path.relative_to(root))]=_sha(path)
    return {'schema':SCHEMA,'interpreter':info,
        'executables':[{'path':name,'resolved':str(Path(name).resolve()),'sha256':_sha(Path(name))} for name in EXECUTABLES],
        'stdlib_root':str(root),'stdlib_files_sha256':files,
        'stdlib_tree_sha256':hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()}


def verify(expected):
    if not isinstance(expected,dict) or expected.get('schema')!=SCHEMA:
        raise ValueError('Invalid qualified judge environment')
    if capture()!=expected:
        raise ValueError('Qualified judge environment changed')
