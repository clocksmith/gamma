"""Label-free authority packets to prospective clause records. No source/model."""
import hashlib,json,importlib.util,copy
from pathlib import Path
from projects.algorithm_solver.catalogue.public_batch_adapter import bounded_regular_read
from projects.algorithm_solver.catalogue.boundary_policy import authorize_before_open
BASE=Path(__file__).resolve().parent.parent
_spec=importlib.util.spec_from_file_location('_packet_representation',BASE/'contract-clause-recognition-v1/representation.py');rep=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(rep)
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def pinned(spec):
 b=bounded_regular_read(spec['path'],maximum_bytes=4*1024**2)
 if sha(b)!=spec['sha256']:raise ValueError('pinned artifact drift')
 return json.loads(b)
def load_packets(selection_spec,manifest_spec,packet_spec,gate=None):
 selection=pinned(selection_spec);manifest=pinned(manifest_spec)
 if manifest['selection_freeze_sha256']!=selection_spec['sha256']or manifest['private_artifacts']['authority-contract-packets.json']!=packet_spec['sha256']:raise ValueError('manifest/packet binding')
 ids=selection['selected_problem_ids']
 if len(ids)!=24 or len(set(ids))!=24 or manifest['selected_problem_ids']!=ids:raise ValueError('exact24 caller-selected membership')
 cfg=pinned(dict(path=selection['gate_config_path'],sha256=selection['gate_config_sha256']))
 def live(pid):
  if gate is not None:gate(pid)
  else:authorize_before_open(pid,cfg['artifact_paths'],cfg['trusted_hashes'],language='javascript',payload_kind='statement')
 # ALL selected identities gate before opening the aggregate payload.
 for pid in ids:live(pid)
 rows=pinned(packet_spec)
 if not isinstance(rows,list)or len(rows)!=24 or len({r['problem_id']for r in rows})!=24 or set(r['problem_id']for r in rows)!=set(ids):raise ValueError('packet membership differs from caller authority')
 expected={r['problem_id']:r for r in manifest['contract_identities']};byid={r['problem_id']:r for r in rows};out=[]
 for pid in ids:
  live(pid);r=byid[pid];c=r['contract'];identity=expected[pid];h=sha(canonical(c))
  if c['problem_id']!=pid or h!=r['contract_sha256']or h!=identity['reviewed_contract_sha256']or c['statement_sha256']!=identity['statement_sha256']or c['authority_evidence_sha256']!=identity['authority_evidence_sha256']or r['catalogue_problem_contract_sha256']!=identity['catalogue_problem_contract_sha256']:raise ValueError('per-ID authority identity mismatch')
  out.append(r)
 return out

def leaves(value,path):
 if isinstance(value,str):
  if value.strip():yield path,value
 elif isinstance(value,dict):
  for k,v in sorted(value.items()):yield from leaves(v,path+'/'+k.replace('~','~0').replace('/','~1'))
 elif isinstance(value,list):
  for i,v in enumerate(value):yield from leaves(v,path+'/'+str(i))
 # Non-string scalar fields are deliberately not fabricated into text spans.

def clause_records(packet):
 c=packet['contract'];fields={};specs=[];origins={}
 def add(value,path,role,kind):
  for pointer,text in leaves(value,path):
   fields[pointer]=text;origins[pointer]=kind;specs.append(dict(field=pointer,span=[0,len(text)],role=role,polarity=1,required=False))
 domain=c.get('domain')
 if isinstance(domain,dict):
  for k,v in sorted(domain.items()):
   if k!='invalid_input_policy':add(v,'/domain/'+k,'preconditions','official_domain')
 else:add(domain,'/domain','input_domain','official_domain')
 result=c.get('result')
 if isinstance(result,dict):
  if 'objective'in result:add(result['objective'],'/result/objective','objective','official_result')
  if 'domain'in result:add(result['domain'],'/result/domain','output_shape','official_result')
 else:add(result,'/result','objective','official_result')
 effects=c.get('local_effects',{})
 for k in ('policy','inputs','mutable_return'):
  if k in effects:add(effects[k],'/local_effects/'+k,'effects','explicit_local_policy_not_official_mandate')
 authority=dict(problem_id=packet['problem_id'],fields=fields,clauses=specs)
 rows=rep.clauses(authority,packet['contract_sha256'])
 for row in rows:row.update(authority_field_kind=origins[row['field']],packet_contract_sha256=packet['contract_sha256'],obligation_purpose='UNKNOWN',polarity_semantics='Affirmative inclusion of entire verbatim clause; internal negation not parsed',required_status='UNKNOWN; false is not an absence claim')
 return rows

def artifact_context(packet):
 c=packet['contract'];result=c.get('result')
 return dict(problem_id=packet['problem_id'],reviewed_contract_sha256=packet['contract_sha256'],catalogue_problem_contract_sha256=packet['catalogue_problem_contract_sha256'],declared_domain=c.get('domain'),declared_interface=c.get('interface'),declared_local_effects=c.get('local_effects'),finite_evidence_scope=result.get('finite_evidence_scope')if isinstance(result,dict)else None,qualification_scope=copy.deepcopy(packet.get('qualification_scope')),qualification_scope_status='PRESERVED'if 'qualification_scope'in packet else'UNKNOWN',artifact_applicability='UNASSESSED',semantic_similarity_grants_delivery=False)

def revision(stable_ids,unchanged_documents_sha256,unchanged_index_sha256,clauses,packet_sha256):
 if len(stable_ids)!=4081 or any(not isinstance(x,str)or not x for x in stable_ids)or len(set(stable_ids))!=4081:raise ValueError('all4081 original rival identities required')
 if any(c['problem_id']not in set(stable_ids)for c in clauses):raise ValueError('clause outside universe')
 record=dict(schema='gamma.prospective-clause-revision.v1',stable_ids=list(stable_ids),unchanged102_documents_sha256=unchanged_documents_sha256,unchanged4081_index_sha256=unchanged_index_sha256,packet_sha256=packet_sha256,clause_ids=sorted(c['clause_id']for c in clauses),clause_records_sha256=sha(canonical(sorted(clauses,key=lambda c:c['clause_id']))),artifact_applicability_granted=False)
 return record,sha(canonical(record))
