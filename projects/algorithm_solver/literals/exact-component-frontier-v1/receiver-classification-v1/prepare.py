"""Exact209 live-gated source-as-data packet; no cases or candidate execution."""
import hashlib,json,os,pathlib,resource,sys,time
HERE=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));import run_js_global as owner
LOG=pathlib.Path('/workspace/shared/gamma-current875-ast-inventory-20261025-2222/native-v3/worker.log');LOG_SHA='30bfb5b2054751caeca1d2802abc23e1b104b205f65ea994645632b309177f96'
def main():
 os.umask(0o077);resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60));start=time.monotonic();dest=pathlib.Path(sys.argv[1]);raw=LOG.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=LOG_SHA:raise ValueError('prior AST metadata drift')
 allowed={'unsupported_CallExpression','non_length_named_property','unresolved_global_reference','unsupported_NewExpression','string_or_regex_value'}
 rows=[r for r in map(json.loads,raw.splitlines())if 'key'in r and set(r.get('rejection_reasons',[]))<=allowed and r['index_proof']['all_computed_indices_inductively_numeric']]
 if len(rows)!=209 or len({r['problem_id']for r in rows})!=116:raise ValueError('exact209/116 scope')
 base=owner.pinned(owner.BASE,owner.BASE_SHA);config=owner.pinned(owner.CONFIG,owner.CONFIG_SHA);spec=config['source_access']['boundary_gate'];gate=owner.pinned(spec['path'],spec['sha256']);owner.KnownSpecService.from_config(owner.CONFIG,owner.CONFIG_SHA);variants=[];transfer=owner.f.load('receiver_classification_transfer',owner.f.LIT/'readable-joint-blocks-v1/transfer.py')
 for r in rows:
  if time.monotonic()-start>50:raise TimeoutError('bounded preparation')
  b=base['source_rows'][r['key']]
  if b['sha256']!=r['source_sha256']or base['owners'][r['key']]!=r['problem_id']:raise ValueError('AST/frozen source mismatch')
  owner.boundary_policy.authorize_before_open('leetcode:'+r['problem_id'],gate['artifact_paths'],gate['trusted_hashes'],language='javascript',payload_kind='source')
  p=pathlib.Path(b['path'])
  if not p.is_absolute()or any(q.is_symlink()for q in(p,*p.parents)):raise ValueError('source path identity')
  source=transfer.read_relative(p.parent,p.name,maximum=65536)
  if hashlib.sha256(source).hexdigest()!=r['source_sha256']:raise ValueError('exact source drift')
  variants.append({'key':r['key'],'problem_id':r['problem_id'],'source_sha256':r['source_sha256'],'source':source.decode()})
 total=sum(len(v['source'].encode())for v in variants)
 if total!=50555:raise ValueError('exact source mass')
 dest.mkdir(mode=0o700,exist_ok=False);packet={'owners':116,'source_bytes':total,'variants':variants};raw=(json.dumps(packet,sort_keys=True,separators=(',',':'))+'\n').encode();(dest/'inputs.private.json').write_bytes(raw)
 receipt={'source_freeze_sha256':owner.BASE_SHA,'config_sha256':owner.CONFIG_SHA,'boundary_config_sha256':spec['sha256'],'metadata_sha256':LOG_SHA,'inputs_sha256':hashlib.sha256(raw).hexdigest(),'inputs_bytes':len(raw),'variants':209,'owners':116,'source_bytes':total,'per_source_live_gates':209,'source_sha256_checks':209,'candidate_execution':False,'cases_opened':0,'wall_seconds':time.monotonic()-start};(dest/'preparation.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
