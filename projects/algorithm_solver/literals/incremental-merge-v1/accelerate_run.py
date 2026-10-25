"""Explicit scorer-engine successor; retains the exact algorithm and prior ledger."""
import argparse,json,shutil
from pathlib import Path
import run as driver
from search import joint
from accelerator import FastGraph,LIBRARY
HERE=Path(__file__).resolve().parent

def prepare(prior,ledger,output):
 old=(prior/'contract.json').read_bytes();c=json.loads(old)
 for name,h in c['code_sha256'].items():
  if joint.b.sha((HERE/name).read_bytes())!=h:raise ValueError('predecessor source changed')
 validation=Path('/workspace/shared/gamma-dot-diagnostics/kernel-validation.json').read_bytes();v=json.loads(validation)
 if not v['exact_rows_equal'] or v['source_variants']!=len(c['source_rows']) or v['source_sha256']!=joint.b.sha((HERE/'score_kernel.c').read_bytes()) or v['binary_sha256']!=joint.b.sha(LIBRARY.read_bytes()):raise ValueError('kernel proof drift')
 c['predecessor_contract_sha256']=joint.b.sha(old)
 c['predecessor_ledger_sha256']=joint.b.sha((ledger/'ledger.jsonl').read_bytes())
 c['predecessor_ledger_path']=str(ledger)
 c['engine_successor']='exact-canonical-C-DP; source-as-data only; unchanged growth policy'
 c['kernel_source_sha256']=v['source_sha256'];c['kernel_binary_sha256']=v['binary_sha256'];c['kernel_validation_sha256']=joint.b.sha(validation)
 c['code_sha256'].update({n:joint.b.sha((HERE/n).read_bytes()) for n in ['accelerator.py','accelerate_run.py','score_kernel.c']})
 output.mkdir(parents=True,exist_ok=False);joint.b.write(output/'contract.json',c)

def run(freeze,output,capacity,cpu):
 c=json.loads((freeze/'contract.json').read_text())
 if joint.b.sha(LIBRARY.read_bytes())!=c['kernel_binary_sha256'] or joint.b.sha((HERE/'score_kernel.c').read_bytes())!=c['kernel_source_sha256']:raise ValueError('kernel identity mismatch')
 if not output.exists():
  output.mkdir()
  if capacity==128:
   old=Path(c['predecessor_ledger_path'])
   if joint.b.sha((old/'ledger.jsonl').read_bytes())!=c['predecessor_ledger_sha256']:raise ValueError('predecessor ledger drift')
   for n in ['ledger.jsonl','costs.jsonl']:shutil.copyfile(old/n,output/n)
 driver.joint.compact.Graph=FastGraph
 return driver.run(freeze,output,capacity,cpu)

if __name__=='__main__':
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
 f=sub.add_parser('prepare');f.add_argument('--prior',type=Path,required=True);f.add_argument('--ledger',type=Path,required=True)
 r=sub.add_parser('run');r.add_argument('--freeze',type=Path,required=True);r.add_argument('--capacity',type=int,choices=[128,256],required=True);r.add_argument('--cpu-seconds',type=int,default=240)
 for s in (f,r):s.add_argument('--output',type=Path,required=True)
 a=p.parse_args();print(json.dumps(prepare(a.prior,a.ledger,a.output) if a.command=='prepare' else run(a.freeze,a.output,a.capacity,a.cpu_seconds)))
