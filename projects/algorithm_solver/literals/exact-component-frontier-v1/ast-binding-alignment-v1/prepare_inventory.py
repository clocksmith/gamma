"""Approved current875 fit-only source packet preparation; no candidate execution."""
import argparse,hashlib,json,os,resource,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import run_js_global as owner

def main(output):
 os.umask(0o077);resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(60,60));start=time.monotonic()
 base=owner.pinned(owner.BASE,owner.BASE_SHA);config=owner.pinned(owner.CONFIG,owner.CONFIG_SHA)
 spec=config['source_access']['boundary_gate'];gate=owner.pinned(spec['path'],spec['sha256'])
 owner.KnownSpecService.from_config(owner.CONFIG,owner.CONFIG_SHA)
 if len(base['source_rows'])!=875 or len(base['references'])!=300:raise ValueError('fixed current fit scope drift')
 variants=[]
 for key,row in sorted(base['source_rows'].items()):
  if time.monotonic()-start>50:raise TimeoutError('bounded inventory source preparation')
  pid=base['owners'][key]
  owner.boundary_policy.authorize_before_open('leetcode:'+pid,gate['artifact_paths'],gate['trusted_hashes'],language='javascript')
  path=Path(row['path'])
  if not path.is_absolute() or any(p.is_symlink()for p in (path,*path.parents)):raise ValueError('source path identity rejected')
  raw=path.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('frozen qualified source drift')
  variants.append({'key':key,'problem_id':pid,'source_sha256':row['sha256'],'source':raw.decode('utf8')})
 if set(x['problem_id']for x in variants)!=set(base['references']):raise ValueError('owner coverage drift')
 output.mkdir(mode=0o700,parents=True,exist_ok=False)
 packet={'schema':'gamma.current875.ast-inventory-input.v1','fit_problems':300,'variants':variants};raw=(json.dumps(packet,sort_keys=True,separators=(',',':'))+'\n').encode();(output/'inputs.private.json').write_bytes(raw)
 receipt={'schema':'gamma.current875.ast-inventory-preparation.v1','fit_problems':300,'variants':875,'source_pool_freeze_sha256':owner.BASE_SHA,'live_gate_config_sha256':spec['sha256'],'inputs_sha256':hashlib.sha256(raw).hexdigest(),'inputs_bytes':len(raw),'code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(HERE.iterdir())if p.is_file() and p.suffix in ('.mjs','.py')},'wall_seconds':time.monotonic()-start,'candidate_executions':0,'transformed_sources':0,'private_sources_not_for_publication':True}
 (output/'preparation.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items()if k!='code_sha256'},sort_keys=True))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
