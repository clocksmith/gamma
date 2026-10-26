"""Existing source-free JS receipt adapter; extract exact original123 only."""
import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];sys.path.insert(0,str(ROOT/'projects/algorithm_solver'))
from catalogue.javascript_receipt_adapter import adapt_files
REPORT=Path('/workspace/shared/gamma-dot-diagnostics/baseline400-20261025/report.json')
VERIFIED=Path('/workspace/shared/gamma-dot-diagnostics/baseline400-verified.json')
PINS={REPORT:'d29f486ad6626aab02685c50500f02953052f3cf8c918a13fa867b1b820c51e3',REPORT.parent/'contract.json':'7330ebe991a17a37ae0d9661599cd5ee2da312fc6fb64b9144b1087e1778cc7c',VERIFIED:'f37dba3c0a5e051aa6bc8377de8ef2c39ec7384e615a43be869ba0792ecfad41'}
def original123(spec,root,manifest):
 for p,h in PINS.items():
  if hashlib.sha256(p.read_bytes()).hexdigest()!=h:raise ValueError('historical baseline metadata pin')
 c=json.loads((REPORT.parent/'contract.json').read_bytes())
 if c['input_manifest_sha256']!=manifest:raise ValueError('original allowed manifest mismatch')
 allowed=set(spec['partition']['dev_fit'])|set(spec['partition']['dev_val']);sources={};refs={}
 for row in spec['files']:
  if row['kind']=='source':
   pid=row['id'];sources[str(pid)]=[dict(label='original',evidence='baseline',sha256=row['sha256'],path=str(root/row['path']))];refs[str(pid)]='original'
 result=adapt_files(REPORT,VERIFIED,PINS[VERIFIED],allowed,sources,refs,identity_map={p:'leetcode:'+str(p)for p in c['ids']})
 impl=result['implementations']['leetcode:123'];bindings=result['binding_descriptors']['leetcode:123'];receipt=result['verified_receipts'][impl['receipt_sha256']]
 return {'implementation':impl,'bindings':bindings,'receipt':receipt,'metadata_pins':{str(p):h for p,h in PINS.items()},'new_source_case_or_baseline_reads':0,'new_candidate_executions':0}
