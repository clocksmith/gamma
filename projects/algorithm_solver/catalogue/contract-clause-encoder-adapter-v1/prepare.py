"""Importable owner-invoked label-free preparation; freeze verified before siblings."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
from projects.algorithm_solver.catalogue.public_batch_adapter import bounded_regular_read
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
def sha(data):return hashlib.sha256(data).hexdigest()
def pinned(spec):
 raw=bounded_regular_read(spec['path'],maximum_bytes=4*1024**2)
 if sha(raw)!=spec['sha256']:raise ValueError('pin mismatch')
 return json.loads(raw)
def verify_freeze(spec):
 f=pinned(spec)
 for base,key in ((HERE,'files'),(BASE,'dependency_code_sha256')):
  for name,h in f[key].items():
   if Path(name).is_absolute()or '..'in Path(name).parts:raise ValueError('invalid code pin path')
   if sha(bounded_regular_read(str(base/name),maximum_bytes=4*1024**2))!=h:raise ValueError('code/dependency drift')
 return f
def sibling(name):
 spec=importlib.util.spec_from_file_location('_label_free_'+name,HERE/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def prepare(freeze_spec):
 f=verify_freeze(freeze_spec);packets_module=sibling('packets');enc=sibling('encoder_binding');plan=pinned(f['preparation_plan'])
 packets=packets_module.load_packets(plan['selection'],plan['manifest'],plan['packets'])
 index=pinned(plan['original_index_metadata']);descriptor=index['index']
 if sha(packets_module.canonical(descriptor))!=plan['base_index_descriptor_sha256']:raise ValueError('original universe/index metadata drift')
 ids=descriptor['stable_ids'];rows=[c for p in packets for c in packets_module.clause_records(p)]
 record,digest=packets_module.revision(ids,plan['unchanged102_documents_sha256'],plan['unchanged102_index_revision_sha256'],rows,plan['packets']['sha256'])
 return dict(schema='gamma.label-free-clause-preparation.v1',freeze_sha256=freeze_spec['sha256'],revision=record,revision_sha256=digest,prompt_sha256=enc.PROMPT_SHA256,clauses=rows,encoder_inputs=enc.clause_inputs(rows),artifact_contexts=[packets_module.artifact_context(p)for p in packets],encoder_executions=0,artifact_applicability_granted=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--freeze',required=True);p.add_argument('--freeze-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args();result=prepare(dict(path=str(Path(a.freeze).absolute()),sha256=a.freeze_sha256));out=Path(a.output)
 with out.open('x')as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
