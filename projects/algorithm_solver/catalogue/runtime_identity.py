"""Read-only comparison of recorded interpreter/sandbox identities on serving host.

Run on the actual approved desktop, not a different execution namespace. This
probe does not execute candidates or prove an end-to-end serving release.
"""
import argparse
import dataclasses
import hashlib
import json
from pathlib import Path
from ..algsolve.judge import pinned_runtime, sandbox


def attest(javascript_bindings, python_bindings, node_path, python_path=Path('/usr/bin/python3')):
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    current_node=pinned_runtime.freeze_runtime(Path(node_path))
    for binding in javascript_bindings.values():
        if binding['runtime']['manifest']!=current_node:
            raise ValueError('recorded Node dependency/isolation identity differs')
    python_hash=sha(python_path);sandbox_hash=sha(sandbox.__file__);configured_profiles=[]
    for binding in python_bindings.values():
        runtime=binding['runtime']
        if runtime['python_executable_sha256']!=python_hash or runtime['sandbox_sha256']!=sandbox_hash:
            raise ValueError('recorded Python/sandbox identity differs')
        configured=dataclasses.asdict(sandbox.Limits(**runtime['limits']))
        if any(configured[k]!=v for k,v in runtime['limits'].items()):
            raise ValueError('recorded resource configuration differs')
        if configured not in configured_profiles:configured_profiles.append(configured)
    return {'schema':'gamma.catalogue-native-runtime-identity.v1','status':'verified',
            'javascript_source_bindings':len(javascript_bindings),'python_source_bindings':len(python_bindings),
            'node_sha256':current_node['node_sha256'],'python_sha256':python_hash,'sandbox_sha256':sandbox_hash,
            'configured_recorded_profiles':configured_profiles,'limits_execution_enforced_in_this_probe':False,
            'current_recorded_runtime_identity_matches':True,'source_execution_performed':False,
            'new_case_reads':0,'protected_access':False,'current_full_serving_release_qualified':False}


def main():
    p=argparse.ArgumentParser()
    for name in ('javascript-bindings','python-bindings','node','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    js=json.loads(a.javascript_bindings.read_bytes())['binding_descriptors'];py=json.loads(a.python_bindings.read_bytes())['binding_descriptors']
    report=attest(js,py,a.node)
    a.output.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
