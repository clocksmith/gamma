"""Validate the fixed670 measured execution boundary without importing artifacts."""
from pathlib import Path
import dataclasses,hashlib,json,os,sys,re
from algsolve.judge import sandbox
PATHS={'python':'/usr/bin/python3','node':'/usr/bin/node','bwrap':'/usr/bin/bwrap','prlimit':'/usr/bin/prlimit'}
ENV={'PATH':'/usr/bin','PYTHONHASHSEED':'0','PYTHONDONTWRITEBYTECODE':'1','HOME':'/tmp','LANG':'C.UTF-8'}
COMMANDS={'javascript':['/usr/bin/node','--jitless','--max-old-space-size=64','harness.cjs'],'python':['/usr/bin/python3','harness.py']}
LIMITS=sandbox.Limits(wall_seconds=8,cpu_seconds=3,memory_bytes=1024**3,max_output_bytes=4*1024**2)
def need(ok,message):
 if not ok:raise ValueError(message)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def file_identity(path):
 original=Path(path).absolute();remaining=list(original.parts[1:]);current=Path('/');links=[]
 while remaining:
  part=remaining.pop(0)
  if part in ['', '.']:continue
  if part=='..':current=current.parent;continue
  candidate=current/part
  if candidate.is_symlink():
   need(len(links)<40,'Symlink loop');target=os.readlink(candidate);links.append({'path':str(candidate),'target':target});pieces=list(Path(target).parts)
   if os.path.isabs(target):current=Path('/');pieces=pieces[1:]
   remaining=pieces+remaining
  else:current=candidate
 need(original.resolve(strict=True)==current,'Unresolved executable mapping')
 return {'path':str(original),'resolved':str(current),'sha256':sha(current),'symlink_chain':links}
def verify(manifest):
 need(manifest.get('schema')=='algsolve.execution-toolchain.v1','Missing measured execution toolchain')
 need(set(manifest.get('executables',{}))==set(PATHS),'Four executable identities required')
 need(manifest.get('commands')==COMMANDS and manifest.get('child_environment')==ENV and manifest.get('limits')==dataclasses.asdict(LIMITS),'Toolchain invocation/environment/limit changed')
 need(manifest.get('bwrap_argv_templates')=={name:sandbox.bwrap_argv(Path('/MEASURED-RANDOM-TASK-DIRECTORY'),LIMITS,argv) for name,argv in COMMANDS.items()},'Sandbox boundary argv changed')
 measured=[]
 for name,path in PATHS.items():
  row=manifest['executables'][name];need(row.get('path')==path,'Wrong executable path');measured.append({k:row[k] for k in ['path','resolved','sha256','symlink_chain']})
  version=row.get('version',{});need(version.get('argv')==[path,'--version'] and type(version.get('returncode')) is int and version['returncode']==0 and type(version.get('stdout')) is str and bool(version['stdout'].strip()),'Missing successful version measurement')
  dependencies=row.get('dependencies');need(type(dependencies) is list and bool(dependencies),'Missing measured loader dependencies');ldd=row.get('ldd',{})
  need(ldd.get('argv')==['/usr/bin/ldd',path] and type(ldd.get('returncode')) is int and ldd['returncode']==0 and type(ldd.get('stdout')) is str and 'not found' not in ldd['stdout'],'Unresolved dependency measurement')
  reported={row['loader']['path']}
  for line in ldd['stdout'].splitlines():
   match=re.search(r'=>\s+(/\S+)',line) or re.match(r'\s*(/\S+)',line)
   if match:reported.add(match.group(1))
  need({item['path'] for item in dependencies}==reported and len(dependencies)==len(reported),'Missing/duplicate resolved ldd dependency')
  measured+=dependencies+[row['loader']]
  need(row['loader'] in dependencies and 'Requesting program interpreter: '+row['loader']['path'] in row.get('elf_interpreter_line',''),'Unbound ELF loader')
 host=manifest.get('host_runner_python');need(host==file_identity(sys.executable) and host['resolved']==manifest['executables']['python']['resolved'] and host['sha256']==manifest['executables']['python']['sha256'],'Host intake/runner Python identity mismatch');measured.append(host)
 modules=manifest.get('numeric_json_modules',{});need({'json','re','contextlib','_json'}<=set(modules),'Numeric/JSON module boundary missing')
 for name,row in modules.items():
  need(name in ['json','re','contextlib','_json'] or name.startswith('json.') or name.startswith('re.'),'Unsupported module measurement')
  module=sys.modules.get(name);need(module is not None and str(module.__spec__.origin)==row.get('origin'),'Loaded module origin changed')
  if 'file' in row:need(row['file']['resolved']==str(Path(module.__file__).resolve()),'Module file changed');measured.append(row['file'])
  else:need(row=={'origin':'built-in','bound_executable':'python'},'Unbound built-in module')
 measured += list(manifest.get('measurement_tools',{}).values())+[manifest['sandbox_module']]
 need(manifest['sandbox_module']==file_identity(sandbox.__file__),'Sandbox implementation changed')
 for item in measured:need(item==file_identity(item['path']),'Measured executable/library/module/link changed')
 need(type(manifest.get('host_environment')) is dict and type(manifest.get('serial_cpu_affinity')) is list and len(manifest['serial_cpu_affinity'])==1,'Missing execution environment/serial affinity')
 return measured
