#!/usr/bin/env python3
"""Offline-first, non-destructive study catalogue migration; see README.md."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
from urllib.parse import quote

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from schema import SCHEMA
import embeddings
STAGES=('inventory','extract','resolve-identities','convert','validate','build-catalogue','build-embeddings','reconcile')
SOURCE_BASES=('catalogue/authored','catalogue/candidates','literals/paired-authoring-v1','literals/guides-qualified-v1/sources')

def source_label(path):
 name=Path(path).name
 if re.fullmatch(r'[a-f0-9]{24}\.(py|js)',name):return Path(path).stem
 match=re.match(r'^(\d+)(?:\.|-)',name)
 return match[1] if match else None

def source_files(root):
 for base in SOURCE_BASES:
  for p in sorted(Path(root,'projects/algorithm_solver',base).rglob('*')):
   if p.is_file() and p.suffix in ('.py','.js') and any(lang in p.parts for lang in ('python','javascript')) and source_label(p) is not None:yield p

def source_metadata_files(root):
 authored=Path(root,'projects/algorithm_solver/catalogue/authored')
 for p in sorted(authored.glob('source-completion*/manifest.json')):yield p,'gamma-paired-manifest'
 for p in sorted(authored.glob('hack2hire-worklists-*/*')):
  if p.is_file() and (p.suffix in ('.txt','.md')):yield p,'hack-worklist'
 for name in ('manifest.json','design.json','semantics.json','contracts.json','study-content.json','study-examples.json'):
  for p in sorted(authored.glob('*/'+name)):
   if name=='manifest.json' and p.parent.name.startswith('source-completion'):continue
   yield p,'gamma-source-metadata'
 for p in sorted(authored.glob('*/semantics/*.json')):yield p,'gamma-source-metadata'
 for p in sorted(authored.glob('*/study-records/*.json')):yield p,'gamma-study-record'

def record_refs(value):
 if isinstance(value,dict):
  if set(value)=={'kind','id','version','path','sha256'}:yield value
  else:
   for child in value.values():yield from record_refs(child)
 elif isinstance(value,list):
  for child in value:yield from record_refs(child)

def encoded(value):return (json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def decode(raw):
 def pairs(items):
  result={}
  for key,value in items:
   if key in result:raise ValueError('Duplicate JSON key: '+key)
   result[key]=value
  return result
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda value:(_ for _ in ()).throw(ValueError('Nonfinite JSON: '+value)))
def read(path):return decode(Path(path).read_text())
def write(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);raw=encoded(value);temporary=path.with_suffix(path.suffix+'.next');temporary.write_bytes(raw);os.replace(temporary,path)
def slug(value):return quote(value,safe='-_.')
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],text=True,stderr=subprocess.DEVNULL).strip()
def within(root,path):
 root=Path(root).resolve();path=Path(path).resolve()
 if path!=root and root not in path.parents:raise ValueError('path leaves declared root: '+str(path))
 return path

def missing(reason):return {'status':'missing','reason':reason}
def unknown(reason):return {'status':'unknown','reason':reason}
def na(reason):return {'status':'not-applicable','reason':reason}
def present(value,pointer):return {'status':'present','value':value,'provenance':[pointer]}
def field(row,key,pointer):return present(row[key],{**pointer,'selector':pointer['selector'].rstrip('/')+'/'+escape(key)}) if key in row and row[key] is not None else missing('Source does not supply '+key)
def escape(value):return str(value).replace('~','~0').replace('/','~1')
def list_field(row,key,pointer):
 value=field(row,key,pointer)
 if value['status']=='present' and not isinstance(value['value'],list):value['value']=[value['value']]
 return value

def pick(row,key,default=None):return row.get(key,default)
def semantic(value,record_root=False):
 if isinstance(value,dict):
  ignored={'origin'} if record_root else set()
  if value.get('status')=='present' and set(value)=={'status','value','provenance'}:ignored.add('provenance')
  return {k:semantic(v) for k,v in value.items() if k not in ignored}
 if isinstance(value,list):return [semantic(v) for v in value]
 return value


class Run:
 def __init__(self,destination):
  self.dest=Path(destination).resolve();self.dest.mkdir(parents=True,exist_ok=True,mode=0o700)
  self._phase_cache={};self.toolchain={}
  for name in ('migrate.py','schema.py','graphs.py','embeddings.py','lucyd-bridge.cjs','legacy/composable-study.v2.schema.json'):
   raw=(HERE/name).read_bytes();digest=sha(raw);relative='tools/'+digest+Path(name).suffix;target=self.dest/relative;target.parent.mkdir(exist_ok=True);target.write_bytes(raw);self.toolchain[name]={'sha256':digest,'snapshot':relative}
  self.config=read(self.dest/'config.json') if (self.dest/'config.json').exists() else None
 def phase(self,name):
  path=self.dest/(name+'.json');raw=path.read_bytes();key=(name,sha(raw))
  if key not in self._phase_cache:self._phase_cache[key]=decode(raw)
  value=self._phase_cache[key]
  if value.get('toolchain')!=self.toolchain:raise ValueError('Stale '+name+' stage: migration tools changed; rerun from inventory')
  for dependency,pin in value.get('dependencies',{}).items():
   if sha((self.dest/(dependency+'.json')).read_bytes())!=pin:raise ValueError('Stale '+name+' stage: rerun after '+dependency+' changed')
   self.phase(dependency)
  return value
 def checkpoint(self,name,value):
  dependencies={'inventory':[],'extract':['inventory'],'resolve-identities':['inventory','extract'],'convert':['inventory','resolve-identities'],'validate':['inventory','convert'],'build-catalogue':['convert','validate'],'build-embeddings':['convert','build-catalogue'],'reconcile':['inventory','extract','convert','validate','build-catalogue','build-embeddings']}
  value={**value,'toolchain':self.toolchain,'dependencies':{d:sha((self.dest/(d+'.json')).read_bytes()) for d in dependencies.get(name,[])}}
  archive=self.dest/'phase-history'/name/(sha(encoded(value))+'.json');archive.parent.mkdir(parents=True,exist_ok=True)
  if not archive.exists():archive.write_bytes(encoded(value))
  write(self.dest/(name+'.json'),value)
 def snapshot(self,item):
  path=within(self.dest,self.dest/item['snapshot']);raw=path.read_bytes()
  if sha(raw)!=item['sha256']:raise ValueError('Input snapshot changed: '+item['id'])
  return raw
 def blob(self,raw,media='application/json',extension='json'):
  digest=sha(raw);relative=f'blobs/{digest}.{extension}';p=self.dest/relative
  if p.exists() and p.read_bytes()!=raw:raise ValueError('Content-addressed blob conflict')
  if not p.exists():p.parent.mkdir(exist_ok=True);p.write_bytes(raw)
  return {'path':relative,'sha256':digest,'bytes':len(raw),'mediaType':media}
 def pointer(self,item,selector=''):
  return {'repository':item['repository'],'revision':item['revision'],'path':item['path'],'sha256':item['sha256'],'selector':selector}

class Writer:
 def __init__(self,run):
  self.run=run;self.previous={};self.records={};self.refs={}
  if (run.dest/'convert.json').exists():
   for ref in read(run.dest/'convert.json')['records']:
    raw=within(run.dest,run.dest/ref['path']).read_bytes()
    if sha(raw)!=ref['sha256']:raise ValueError('Existing version was modified: '+ref['path'])
    self.previous[(ref['kind'],ref['id'])]=(ref,decode(raw))
 def put(self,kind,id,origin,**data):
  key=(kind,id)
  if key in self.refs:raise ValueError('Duplicate record identity during conversion: '+str(key))
  old=self.previous.get(key);base={'schema':'study.record.v1','kind':kind,'id':id,'origin':[origin],**data}
  if old and semantic({k:v for k,v in old[1].items() if k!='version'},True)==semantic(base,True):
   ref=old[0];value=old[1]
  else:
   version=old[0]['version']+1 if old else 1
   while True:
    value={**base,'version':version};raw=encoded(value);relative=f'records/{kind}/{slug(id)}/v{version}.json';p=self.run.dest/relative
    if not p.exists() or p.read_bytes()==raw:break
    version+=1
   p.parent.mkdir(parents=True,exist_ok=True)
   if not p.exists():p.write_bytes(raw)
   ref={'kind':kind,'id':id,'version':version,'path':relative,'sha256':sha(raw)}
  self.records[key]=value;self.refs[key]=ref;return ref
 def artifact(self,id,pointer,type='source-native',title='',value=None,file=None,problem=None,approach=None,contract=None,language=None,document_schema=None,execution='reference-only',external=None,metadata=None):
  if value is not None:file=self.run.blob(encoded(value))
  data=dict(type=type,title=title or id,problemId=problem,approachId=approach,contract=contract,file=present(file,pointer) if file else missing('Payload intentionally not opened or copied'),externalLocator=present(external,pointer) if external is not None else na('Content is copied into the migration destination'),language=language,documentSchema=document_schema,executionKind=execution,complexityClaims=missing('No source-bound complexity claim normalized'),nativeMetadata=present(metadata,pointer) if metadata is not None else missing('No additional metadata'))
  if ('artifact',id) in self.refs:
   existing=self.records['artifact',id]
   if any(semantic(existing[k])!=semantic(v) for k,v in data.items()):raise ValueError('Conflicting artifact identity: '+id)
   return self.refs['artifact',id]
  return self.put('artifact',id,pointer,**data)


def inventory(run,args):
 defaults={'gamma':HERE.parents[1],'simulatte':HERE.parents[2]/'simulatte','hatch':HERE.parents[2]/'hatch'}
 roots={k:str(Path(getattr(args,k) or (run.config or {}).get('roots',{}).get(k) or defaults[k]).resolve()) for k in ('gamma','simulatte','hatch')}
 args.gamma_catalogue=args.gamma_catalogue or (run.config or {}).get('gammaCatalogue');args.mesh_session=args.mesh_session or (run.config or {}).get('meshSession')
 for root in roots.values():
  if not Path(root,'AGENTS.md').exists():raise ValueError('Missing owning repository instructions: '+root)
 # Output is never an existing repository or one of the live source directories.
 for root in roots.values():
  if run.dest==Path(root) or Path(root) in run.dest.parents:raise ValueError('Use a destination outside the input repositories')
 run.config={'schema':'study.migration-config.v1','roots':roots,'gammaCatalogue':str(Path(args.gamma_catalogue).resolve()) if args.gamma_catalogue else None,'meshSession':str(Path(args.mesh_session).resolve()) if args.mesh_session else None}
 write(run.dest/'config.json',run.config);items=[];indexes={};heads={repo:git(root,'rev-parse','HEAD') for repo,root in roots.items()}
 for repo,root in roots.items():
  rows=git(root,'ls-files','-s').splitlines();indexes[repo]={}
  for row in rows:
   meta,path=row.split('\t',1);indexes[repo][path]=meta.split()[1]
 def add(repo,relative,role,open_payload=True,absolute=None):
  root=Path(roots[repo]);p=within(root,root/relative) if absolute is None else Path(absolute).resolve()
  if not p.is_file():return
  item={'id':repo+':'+relative,'repository':repo,'path':relative,'role':role,'bytes':p.stat().st_size,'mtimeNs':str(p.stat().st_mtime_ns),'gitObject':indexes[repo].get(relative),'repositoryHead':heads[repo]}
  if open_payload:
   if item['bytes']>64*1024**2:raise ValueError('Metadata input exceeds explicit 64 MiB bound: '+relative)
   raw=p.read_bytes();digest=sha(raw);oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
   item.update(sha256=digest,revision='git-blob:'+oid if oid==item['gitObject'] else 'working-tree:'+digest,snapshot='source-cache/'+repo+'/'+digest+p.suffix)
   target=run.dest/item['snapshot'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
  else:item.update(sha256=None,revision='git-blob:'+item['gitObject'] if item['gitObject'] else None,snapshot=None)
  items.append(item)
 for path,role in [('projects/question_bank/hack2hire/bank.json','hack-bank'),('projects/question_bank/hack2hire/descriptions.json','hack-descriptions'),('projects/question_bank/hack2hire/leetcode-metadata.json','leetcode-metadata')]:add('gamma',path,role)
 # Enumerating source filenames reads no candidate/source/test bytes.
 for p in source_files(roots['gamma']):add('gamma',str(p.relative_to(roots['gamma'])),'gamma-source',False)
 # Assignment lists and incoming metadata are retained, not promoted to specifications.
 for p,role in source_metadata_files(roots['gamma']):add('gamma',str(p.relative_to(roots['gamma'])),role)
 if args.gamma_catalogue:add('gamma','explicit-private-catalogue.json','gamma-catalogue',absolute=args.gamma_catalogue)
 for path,role in [('problems.json','lucyd-problems'),('interview-problems.json','lucyd-compatibility'),('interview-journeys.json','lucyd-compatibility'),('interview-solutions.json','lucyd-compatibility'),('learning-journeys.json','lucyd-compatibility'),('composable-solutions/manifest.json','lucyd-manifest'),('class-library.json','lucyd-library'),('config.json','lucyd-config')]:add('simulatte','public/data/system-diagram/'+path,role)
 for p in sorted(Path(roots['simulatte'],'public/data/system-diagram/composable-solutions').glob('*.json')):
  if p.name not in ('manifest.json',):add('simulatte',str(p.relative_to(roots['simulatte'])),'lucyd-component-library' if p.name=='components.json' else 'lucyd-study' if p.name!='problem.schema.json' else 'lucyd-schema')
 for p in sorted(Path(roots['simulatte'],'public/data/system-diagram/classes').glob('*.json')):add('simulatte',str(p.relative_to(roots['simulatte'])),'lucyd-library')
 for name in ('architecture-model.js','architecture-adapters.js','diagram.js','class-library.js','subsystems.js','study/composable-study.js'):add('simulatte','public/simulatte/system-diagram/'+name,'lucyd-validator')
 for p in sorted(Path(roots['simulatte'],'public/data/system-diagram').glob('*.enc.json')):add('simulatte',str(p.relative_to(roots['simulatte'])),'encrypted-collection',False)
 for path in ('mesh/server.mjs','mesh/gamma-catalogue.mjs','mesh/gamma-guides.mjs','mesh/lucyd.mjs','mesh/README.md'):add('hatch',path,'mesh-integration')
 if args.mesh_session:add('hatch','explicit-private-session.json','mesh-session',absolute=args.mesh_session)
 result={'schema':'study.inventory.v1','items':items,'counts':dict(Counter(x['role'] for x in items)),'casePayloadReads':0,'candidatePayloadReads':0,'consumerChanges':0}
 run.checkpoint('inventory',result);return result


def extract(run,args):
 inv=run.phase('inventory');tasks=[];dispositions=[];by_role=defaultdict(list)
 for item in inv['items']:by_role[item['role']].append(item)
 def task(adapter,item,selector,data):tasks.append({'adapter':adapter,'inputId':item['id'],'selector':selector,'data':data})
 for item in inv['items']:
  role=item['role']
  if item['snapshot'] is None:
   state='blocked' if role=='encrypted-collection' else 'referenced';reason='Encrypted collection was not unlocked' if state=='blocked' else 'Filename/Git identity only; candidate source bytes stay unopened'
   dispositions.append({'inputId':item['id'],'status':state,'reason':reason})
   if role=='gamma-source':task('gamma-source',item,'',{'path':item['path'],'gitObject':item['gitObject'],'bytes':item['bytes']})
   continue
  raw=run.snapshot(item)
  if role=='hack-bank':
   data=decode(raw)
   if not isinstance(data.get('records'),list):raise ValueError('Unsupported Hack2Hire bank')
   for i,row in enumerate(data['records']):task('hack',item,f'/records/{i}',row)
  elif role=='leetcode-metadata':
   for i,row in enumerate(decode(raw)):task('leetcode',item,f'/{i}',row)
  elif role=='lucyd-problems':
   for i,row in enumerate(decode(raw)['problems']):task('lucyd-simulation',item,f'/problems/{i}',row)
  elif role=='lucyd-study':
   data=decode(raw)
   if not str(data.get('schema','')).startswith('simulatte.composableStudy.'):
    dispositions.append({'inputId':item['id'],'status':'unsupported','reason':'Not a composable study document'});continue
   task('lucyd-study',item,'',data)
  elif role=='gamma-paired-manifest':
   data=decode(raw)
   if data.get('schema')!='gamma.original-paired-sources.v1':raise ValueError('Unsupported paired manifest')
   for i,row in enumerate(data['problems']):task('gamma-paired',item,f'/problems/{i}',row)
  elif role=='gamma-catalogue':
   data=decode(raw)
   if data.get('schema') not in ('gamma.dual-language-catalogue.v1','gamma.dual-language-catalogue.v2'):raise ValueError('Explicit catalogue is not a recognized metadata-only schema')
   for i,row in enumerate(data['problems']):task('gamma-catalogue',item,f'/problems/{i}',row)
  elif role=='gamma-study-record':
   from jsonschema import Draft202012Validator
   try:
    data=decode(raw);Draft202012Validator(SCHEMA).validate(data)
    if data['kind'] not in ('contract','approach','artifact'):raise ValueError('Authoring intake accepts contracts, approaches and artifacts only; never evidence/admissions')
    task('study-record',item,'',data)
   except Exception as error:
    dispositions.append({'inputId':item['id'],'status':'blocked','reason':'Invalid or unsupported authored record: '+str(error)[:600]});continue
  elif role=='mesh-session':task('mesh-session',item,'',decode(raw))
  dispositions.append({'inputId':item['id'],'status':'converted' if role in ('hack-bank','leetcode-metadata','lucyd-problems','lucyd-study','gamma-paired-manifest','gamma-catalogue','gamma-study-record','mesh-session') else 'referenced','reason':'Source-specific extraction' if role in ('hack-bank','leetcode-metadata','lucyd-problems','lucyd-study','gamma-paired-manifest','gamma-catalogue','gamma-study-record','mesh-session') else 'Preserved native metadata/integration/compatibility input; not another authored catalogue'})
 seen=set()
 for t in tasks:
  d=t['data'];key=(t['adapter'],t['inputId'],d.get('uid') or d.get('problem_id') or d.get('referenceId') or d.get('id') or d.get('problem',{}).get('referenceId'))
  if t['adapter']=='gamma-source':continue
  if key in seen:raise ValueError('Duplicate source record identity: '+str(key))
  seen.add(key)
 result={'schema':'study.extraction.v1','tasks':tasks,'dispositions':dispositions,'counts':dict(Counter(t['adapter'] for t in tasks))};run.checkpoint('extract',result);return result


def resolve(run,args):
 state=run.phase('extract');index={x['id']:x for x in run.phase('inventory')['items']};tasks=[];claims=[];manifest_paths={}
 study_tasks={index[t['inputId']]['path']:t for t in state['tasks'] if t['adapter']=='study-record'};blocked={};dependencies={};identities=defaultdict(list)
 for path,t in study_tasks.items():identities[(t['data']['kind'],t['data']['id'])].append(path)
 for paths in identities.values():
  if len({index[study_tasks[path]['inputId']]['sha256'] for path in paths})>1:
   for path in paths:blocked[path]='Conflicting authored files declare the same record identity; review required'
 for path,t in study_tasks.items():
  dependencies[path]=[]
  for r in record_refs(t['data']):
   target=study_tasks.get(r['path'])
   if target is None:blocked[path]='Referenced authored record is not in the pinned intake: '+r['path'];continue
   item=index[target['inputId']];d=target['data']
   if item['sha256']!=r['sha256'] or (d['kind'],d['id'],d['version'])!=(r['kind'],r['id'],r['version']):blocked[path]='Authored reference identity/version/hash mismatch: '+r['path'];continue
   dependencies[path].append(r['path'])
 visiting=set();finished=set()
 def ready(path):
  if path in blocked:return False
  if path in finished:return True
  if path in visiting:blocked[path]='Cyclic authored record references';return False
  visiting.add(path)
  for target in dependencies[path]:
   if not ready(target):blocked[path]='Blocked authored dependency: '+target;visiting.remove(path);return False
  visiting.remove(path);finished.add(path);return True
 for path in study_tasks:ready(path)
 study_source_paths={}
 for path,t in study_tasks.items():
  d=t['data'];pid=d.get('problemId')
  if pid is None and d.get('contract'):
   dependency=study_tasks.get(d['contract']['path']);pid=dependency['data'].get('problemId') if dependency else None
  if not isinstance(pid,str) or not pid:blocked[path]='Authored record has no declared owning problem identity'
  t['declaredProblemId']=pid
 finished.clear()
 for path in study_tasks:ready(path)
 for path,t in study_tasks.items():
  d=t['data'];pid=t['declaredProblemId']
  if path not in blocked and d['kind']=='artifact' and d['type']=='implementation' and d['file']['status']=='present':
   source_path=d['file']['value']['path'];study_source_paths[source_path]=pid;manifest_paths[source_path]=(pid,d.get('language'))
 for t in state['tasks']:
  if t['adapter']=='gamma-paired':
   for language,source in t['data']['sources'].items():
    source_path=str(Path(index[t['inputId']]['path']).parent/source['path']);manifest_paths[source_path]=(t['data']['problem_id'],language)
 for t in state['tasks']:
  d=t['data'];adapter=t['adapter'];t=dict(t)
  if adapter=='leetcode':pid='leetcode:'+str(d['id'])
  elif adapter in ('lucyd-simulation','lucyd-study'):pid='lucyd:'+(d.get('referenceId') or d['problem']['referenceId'])
  elif adapter=='hack':pid=d['uid']
  elif adapter in ('gamma-paired','gamma-catalogue'):pid=d.get('problem_id')
  elif adapter=='study-record':
   path=index[t['inputId']]['path'];pid=t.get('declaredProblemId') or 'blocked-authored:'+d['id']
   if path in blocked:t['blockedReason']=blocked[path]
  elif adapter=='gamma-source':
   path=d['path'];label=source_label(path);language='python' if '/python/' in path else 'javascript';batch=str(Path(path).parent.parent)
   pid=manifest_paths.get(path,(f'gamma-source:{batch}:{label}',language))[0]
   if path not in manifest_paths:claims.append({'sourceProblem':pid,'candidateExternalId':'hack2hire:'+label if re.fullmatch(r'[a-f0-9]{24}',label) else 'leetcode:'+str(int(label)),'basis':'filename only; identity and exact contract unresolved','mergeAllowed':False})
  else:pid='mesh:session:'+sha(encoded(d))[:20]
  if not isinstance(pid,str) or not pid:raise ValueError('Missing source identity')
  t['problemId']=pid;tasks.append(t)
 result={**state,'schema':'study.identities.v1','tasks':tasks,'studySourcePaths':study_source_paths,'proposedRelationships':claims,'policy':'Only declared source IDs and explicit source mappings join records. No title/similarity merge.'};run.checkpoint('resolve-identities',result);return result


def convert(run,args):
 state=run.phase('resolve-identities');inv=run.phase('inventory');inputs={i['id']:i for i in inv['items']};w=Writer(run);problems={};source_refs={};company_refs={};converted_rows=[];native_files={};details={};paired_paths={}
 for item in inv['items']:
  if item['role']=='hack-descriptions':details={r['source_post_id']:r for r in decode(run.snapshot(item))['records']}
 inventory_raw=(run.dest/'inventory.json').read_bytes()
 def pointer(task):
  item=inputs[task['inputId']]
  if item['sha256']:return run.pointer(item,task['selector'])
  metadata={k:item[k] for k in ('repository','path','bytes','gitObject','revision')};raw=encoded(metadata);digest=sha(raw);relative='source-inventory/'+digest+'.json';destination=run.dest/relative;destination.parent.mkdir(exist_ok=True);destination.write_bytes(raw)
  return {'repository':'migration-inventory','revision':'sha256:'+digest,'path':relative,'sha256':digest,'selector':''}
 def native(task):
  key=(task['inputId'],task['problemId'])
  if key not in native_files:native_files[key]=w.artifact('native:'+sha(encoded(key))[:24],pointer(task),title=task['inputId']+'#'+task['problemId'],value=task['data'])
  return native_files[key]
 def problem(task,title=None,type='unknown',identity='source-declared'):
  pid=task['problemId'];p=pointer(task)
  if pid not in problems:problems[pid]={'origin':p,'title':present(title,p) if title is not None else unknown('Source filename does not establish the official problem title'),'type':type,'topics':missing('Topics not supplied'),'difficulty':missing('Difficulty not supplied'),'aliases':[],'contracts':[],'approaches':[],'artifacts':[],'evidence':[],'sources':[],'companyReports':[],'relationships':[],'identity':{'status':identity,'explanation':'Preserved declared source identity' if identity!='unresolved' else 'Source-local identity only; filename does not prove official frontend ID'}}
  return problems[pid]
 def source(task,title,url=None,type='repository-authored',scope='metadata',license=None):
  key=(task['inputId'],task['problemId'],title,url)
  if key not in source_refs:
   p=pointer(task);source_refs[key]=w.put('source','source:'+sha(encoded(key))[:24],p,title=title,url=url,publisher=unknown('Publisher not separately supplied'),sourceType=type,contentScope=scope,license=present(license,p) if license else unknown('Redistribution license not established'),redistribution='unknown',native=native(task))
  return source_refs[key]
 def company(name,p):
  id='company:'+name.casefold()
  if id not in company_refs:company_refs[id]=w.put('company',id,p,name=name,aliases=[],website=missing('No source website supplied'))
  return company_refs[id]
 def contract(task,suffix,label,statement=None,scope='unknown',requirements=None,constraints=None,assumptions=None,examples=None,interfaces=None,source=None,natives=None):
  p=pointer(task);id=task['problemId']+':contract:'+suffix
  if ('contract',id) in w.refs:return w.refs['contract',id]
  return w.put('contract',id,p,problemId=task['problemId'],variantId=id,variantLabel=present(label,p),statement=present(statement,p) if statement is not None else missing('No complete statement acquired by this source adapter'),contentScope=scope,requirements=present(requirements,p) if requirements is not None else missing('Requirements not supplied for this exact variant'),constraints=present(constraints,p) if constraints is not None else missing('Constraints not supplied for this exact variant'),assumptions=present(assumptions,p) if assumptions is not None else missing('Assumptions not supplied'),clarifyingQuestions=missing('Clarifying questions not supplied'),examples=present(examples,p) if examples is not None else missing('Examples not supplied'),interfaces=interfaces or [],effects=unknown('Native effects retained in source; normalized effect contract not established'),comparison=unknown('No normalized result comparator supplied'),sources=[source] if source else [],native=natives or [native(task)])
 def report(task,c,src,name,attribution='aggregator-reported',claim='asked-in-interview',frequency=None,when=None,metadata=None):
  p=pointer(task);return w.put('company-report','company-report:'+sha(encoded([task['inputId'],task['problemId'],c['id'],name]))[:24],p,company=company(name,p),contract=c,source=src,claim=claim,attribution=attribution,frequency=present(frequency,p) if frequency is not None else unknown('No interpretable source frequency supplied'),reportedAt=present(when,p) if when else missing('No report date supplied'),role=missing('No role supplied'),nativeMetadata=present(metadata,p) if metadata is not None else missing('No additional company-report metadata'))
 def relationship(task,c,target,relation,explanation,srcs):
  return w.put('relationship','relationship:'+sha(encoded([c['id'],target,relation]))[:24],pointer(task),fromContract=c,to=present(target,pointer(task)),relation=relation,explanation=explanation,sources=srcs,evidence=[],mergeAllowed=False)

 # Metadata contracts establish canonical external identities without opening solutions.
 for task in state['tasks']:
  if task['adapter']!='leetcode':continue
  d=task['data'];p=problem(task,d['title'],'coding');src=source(task,d['title'],d.get('url'),'official-problem');c=contract(task,'official-metadata','Official metadata; specification pending',source=src)
  p['contracts'].append(c);p['sources'].append(src);p['aliases'].append({'namespace':'leetcode-slug','value':d['slug']})

 for task in sorted(state['tasks'],key=lambda t:0 if t['adapter']=='gamma-paired' else 2 if t['adapter']=='gamma-source' else 1):
  adapter=task['adapter'];d=task['data'];ptr=pointer(task);pid=task['problemId']
  if adapter=='study-record':continue
  if adapter=='leetcode':converted_rows.append({'inputId':task['inputId'],'selector':task['selector'],'status':'converted','problemId':pid});continue
  if adapter=='hack':
   category=d['category'];p=problem(task,d['title'],{'coding':'coding','sql':'sql','system-design':'system-design','ml-system-design':'ml-design','ml-design':'ml-design','object-oriented-design':'ood','ood':'ood'}.get(category,'unknown'))
   p['topics']=present(d.get('topics',d.get('source_algorithm_tags',[])),ptr);p['difficulty']=field(d,'source_difficulty',ptr);src=source(task,d['title'],d.get('url'),'question-bank','preview' if d.get('source_post_id') in details else 'metadata',d.get('license'));p['sources'].append(src)
   desc=details.get(d.get('source_post_id'),{});preview=desc.get('description',{}).get('excerpt');variants=d.get('variants') or [{'uid':d['uid']+':group','id':'group','ordinal':1}]
   for variant in variants:
    c=contract(task,'hack2hire:'+str(variant['id']),'Reported variant '+str(variant.get('ordinal',variant['id'])),preview,'preview' if preview is not None else 'unknown',source=src);p['contracts'].append(c)
    for name in d.get('companies',[]):p['companyReports'].append(report(task,c,src,name,frequency=(desc.get('source_company_attributes') or {}).get(name,{'source_frequency':d.get('source_frequency')}),when=(desc.get('source_last_report_seen') or {}).get('lastReportSeenDate'),metadata={'scope':'Hack2Hire group association; not independently confirmed for this exact variant','variant':variant}))
    for candidate in d.get('leetcode_overlap',{}).get('candidates',[]):p['relationships'].append(relationship(task,c,candidate,'title-match-candidate','Source title overlap retained without merging contracts',[src]))
    for link in desc.get('source_leetcode_relationships',[]):p['relationships'].append(relationship(task,c,link,'source-cites','Explicit source citation; no equivalence inferred',[src]))
   p['artifacts'].append(native(task))
  elif adapter=='gamma-paired':
   p=problem(task,d['title'],'coding');src=source(task,d['title'],d.get('official_url'),'repository-authored');p['sources'].append(src)
   interfaces=[{'language':lang,'kind':'function','declaration':present({'entrypoint':d['entrypoint'],'parameters':d['parameters'],'returns':d['return']},ptr),'nativeMetadata':present({'definitionResponseSha256':d['definition_response_sha256']},ptr)} for lang in d['sources']]
   batch=str(Path(inputs[task['inputId']]['path']).parent);c=contract(task,'gamma:'+batch,d['title']+' native API',interfaces=interfaces,source=src);p['contracts'].append(c)
   for lang,info in d['sources'].items():
    path=str(Path(batch)/info['path']);paired_paths[path]=(pid,c)
    a=w.artifact('gamma-source:'+path,ptr,type='implementation',title=d['title']+' · '+lang,problem=pid,contract=c,language=lang,execution='code',external={'repository':'gamma','path':path,'declaredSha256':info['sha256'],'binding':'source manifest claim; candidate payload intentionally unopened'},metadata={'status':d['status'],'entrypoint':d['entrypoint']});p['artifacts'].append(a)
   manifest=decode(run.snapshot(inputs[task['inputId']]))
   # Development report is referenced as historical evidence; no new qualification.
   if manifest.get('development_evidence'):
    a=w.artifact('historical:'+sha(encoded([batch,manifest['development_evidence']]))[:24],ptr,type='source-native',title='Author development report reference',external={'repository':'gamma','path':batch+'/'+manifest['development_evidence']['path'],'declaredSha256':manifest['development_evidence']['sha256']},metadata=manifest['development_evidence'])
    e=w.put('evidence','evidence:'+sha(encoded([batch,pid,'author-development']))[:24],ptr,contract=c,subjects=p['artifacts'][-len(d['sources']):],method='historical-report',bindingStatus='partial',bindings=present(manifest['development_evidence'],ptr),results=unknown('Source-bound report has not been independently replayed by migration'),report=a,limitations=['Historical author development evidence only; no qualification or admission promoted'],admissionEffect='none');p['evidence'].append(e)
  elif adapter=='gamma-source':
   if d['path'] in state.get('studySourcePaths',{}):
    converted_rows.append({'inputId':task['inputId'],'selector':'','status':'referenced','problemId':pid,'reason':'Exact source path declared by a validated authored implementation record'});continue
   if d['path'] in paired_paths:
    # The explicit manifest already supplies this source's artifact and mapping.
    converted_rows.append({'inputId':task['inputId'],'selector':'','status':'referenced','problemId':pid,'reason':'Joined by exact path in explicit paired manifest'});continue
   p=problem(task,type='coding',identity='unresolved');src=source(task,'Gamma source-local implementation inventory');p['sources'].append(src)
   c=contract(task,'unresolved-source-contract','Source-local contract; identity/specification unresolved',source=src);p['contracts'].append(c)
   lang='python' if '/python/' in d['path'] else 'javascript';a=w.artifact('gamma-source:'+d['path'],ptr,type='implementation',title=Path(d['path']).name+' · '+lang,problem=pid,contract=c,language=lang,execution='code',external={'repository':'gamma','path':d['path'],'gitObject':d['gitObject'],'bytes':d['bytes'],'binding':'Filename/Git identity only; source and official identity not opened or asserted'});p['artifacts'].append(a)
  elif adapter=='gamma-catalogue':
   p=problem(task,type='coding');src=source(task,'Gamma catalogue metadata snapshot');p['sources'].append(src);c=contract(task,'gamma-catalogue','Historical canonical metadata',source=src);p['contracts'].append(c);a=native(task);p['artifacts'].append(a);implementation_refs=[]
   for language,implementation in d['implementations'].items():
    if implementation.get('source_sha256') or implementation.get('canonical_variant_id'):
     ref=w.artifact('gamma-catalogue:'+pid+':'+language+':'+str(implementation.get('canonical_variant_id') or implementation['source_sha256']),ptr,type='implementation',title=pid+' historical '+language+' source reference',problem=pid,contract=c,language=language,execution='reference-only',external={'canonicalVariantId':implementation.get('canonical_variant_id'),'declaredSourceSha256':implementation.get('source_sha256'),'provenance':implementation.get('provenance'),'binding':'Historical catalogue claim; source and receipt payloads remain unopened'},metadata=implementation);p['artifacts'].append(ref);implementation_refs.append(ref)
   e=w.put('evidence','evidence:gamma-catalogue:'+pid,ptr,contract=c,subjects=implementation_refs,method='historical-report',bindingStatus='unbound',bindings=present({'implementations':d['implementations']},ptr),results=unknown('Historical status labels retained, not requalified'),report=a,limitations=['Migration did not open source/case/receipt payloads or establish active serving'],admissionEffect='none');p['evidence'].append(e)
  elif adapter in ('lucyd-simulation','lucyd-study'):
   study=adapter=='lucyd-study';meta=d['problem'] if study else d;title=meta.get('studyLabel') if study else d['title'];exercise=d.get('details',{}).get('exerciseType') if not study else None;ptype='coding' if exercise in ('systems-coding','coding','algorithm-coding') else 'system-design';p=problem(task,title,ptype)
   if p['type']=='unknown':p['type']=ptype
   src=source(task,title or pid,(d.get('provenance',{}).get('source') or {}).get('url') if not study else None,'authored-practice','full');p['sources'].append(src)
   c=contract(task,'lucyd-'+('study' if study else 'simulation'),title or pid,meta.get('scope') if study else d.get('description'),'authored',requirements=meta.get('requirements') if study else d.get('details',{}).get('requirements'),source=src);p['contracts'].append(c);p['artifacts'].append(native(task))
   if not study and d.get('attribution',{}).get('company'):
    kind=d.get('provenance',{}).get('kind');attr={'company-published':'company-published','candidate-reported':'candidate-reported'}.get(kind,'authored-practice');claim='published-practice-question' if attr=='company-published' else 'asked-in-interview' if attr=='candidate-reported' else 'company-inspired-practice';p['companyReports'].append(report(task,c,src,d['attribution']['company'],attr,claim))
   for solution_index,solution in enumerate(d.get('solutions',[])):
    aid=pid+':'+('study' if study else 'simulation')+':'+solution['id'];stages=[]
    sp={**ptr,'selector':ptr['selector']+'/solutions/'+str(solution_index)}
    for i,stage in enumerate(solution.get('stages',[])):
     stp={**sp,'selector':sp['selector']+'/stages/'+str(i)};sid=aid+':stage:'+stage['id'];stnative=w.artifact(sid+':native',stp,value=stage,problem=pid,approach=aid);artifacts=[];checks=[]
     diagram=stage.get('graph') if study else stage.get('diagram')
     if isinstance(diagram,dict):artifacts.append(w.artifact(sid+':diagram',stp,type='diagram',title=stage.get('title','Stage graph'),value=diagram,problem=pid,approach=aid,contract=c,document_schema='simulatte.composableStudy.graph.v2' if study else diagram.get('schema'),execution='conceptual' if study or stage.get('kind')=='design' else 'simulation'))
     elif diagram is not None:artifacts.append(w.artifact(sid+':diagram',stp,type='diagram',problem=pid,approach=aid,contract=c,external={'repository':'simulatte','declaredLocator':diagram,'binding':'Source-declared diagram reference; not resolved by this adapter'}))
     if 'operations' in stage:artifacts.append(w.artifact(sid+':operations',stp,type='graph-change',value={'operations':stage['operations'],'after':diagram},problem=pid,approach=aid,contract=c,document_schema='simulatte.composableStudy.operation-sequence',execution='conceptual'))
     for j,check in enumerate(stage.get('checks',[])):
      checks.append(w.artifact(sid+':check:'+str(j),stp,type='check',value=check,problem=pid,approach=aid,contract=c))
     for checkid in stage.get('checkIds',[]):
      matches=[x for x in solution.get('acceptanceCases',[]) if x.get('id')==checkid]
      if not matches:raise ValueError('Study stage references missing acceptance case '+checkid)
      checks.append(w.artifact(sid+':check:'+str(checkid),stp,type='check',value=matches[0],problem=pid,approach=aid,contract=c))
     stages.append({'id':sid,'type':'design' if study else 'simulation' if stage.get('kind')=='simulation' else 'reasoning','title':field(stage,'title',stp),'question':field(stage,'question' if study else 'challenge',stp),'explanation':field(stage,'explanation',stp),'rationale':field(stage,'reason' if study else 'rationale',stp),'instructions':field(stage,'instructions',stp),'observations':field(stage,'observe',stp),'hints':field(stage,'hints',stp),'requirementIds':field(stage,'requirementIds',stp),'checks':checks,'artifacts':artifacts,'native':stnative})
    # Preserve APIs, pseudocode, assumptions, and checks even where the normalized
    # teaching fields are incomplete; no source field is discarded from native.
    snative=w.artifact(aid+':native',sp,value=solution,problem=pid,approach=aid)
    if solution.get('workload') is not None:p['artifacts'].append(w.artifact(aid+':workload',sp,type='workload',value=solution['workload'],problem=pid,approach=aid,contract=c))
    p['approaches'].append(w.put('approach',aid,sp,problemId=pid,contract=c,title=field(solution,'title',sp),representation='conceptual-design' if study else 'simulation',explanation=field(solution,'explanation' if 'explanation' in solution else 'boundary',sp),chooseWhen=list_field(solution,'chooseWhen',sp),tradeoffs=field(solution,'tradeoffs',sp),invariants=field(solution,'invariants',sp),hints=field(solution,'hints',sp),stages=stages,sequenceStatus='imported',native=snative))
  elif adapter=='mesh-session':
   p=problem(task,d.get('review',{}).get('title'),'unknown');src=source(task,'Explicit Mesh session export',type='model-generated-session',scope='reference-only');p['sources'].append(src);a=native(task);p['artifacts'].append(a)
   p['evidence'].append(w.put('evidence','evidence:'+pid,ptr,contract=None,subjects=[],method='model-generated-suggestion',bindingStatus='unbound',bindings=missing('Model suggestions are not authored reference solutions'),results=present(d.get('review'),ptr),report=a,limitations=['Imported explicit session only; not correctness evidence or canonical authored content'],admissionEffect='none'))
  converted_rows.append({'inputId':task['inputId'],'selector':task['selector'],'status':'converted','problemId':pid})

 # Input order must not determine shared record identity or duplicate an artifact.
 for item in inv['items']:
  if item['snapshot'] is not None and item['role'] in ('mesh-integration','lucyd-compatibility','lucyd-schema','lucyd-validator','lucyd-library','lucyd-config','lucyd-manifest','lucyd-component-library','hack-descriptions','hack-worklist','gamma-source-metadata','gamma-study-record'):
   ptr=run.pointer(item);w.artifact('input:'+item['id'],ptr,type='integration-reference' if item['role']=='mesh-integration' else 'source-native',title=item['id'],file=run.blob(run.snapshot(item),media='text/javascript' if Path(item['path']).suffix in ('.js','.mjs') else 'text/markdown' if Path(item['path']).suffix=='.md' else 'text/plain' if Path(item['path']).suffix=='.txt' else 'application/json',extension=Path(item['path']).suffix.lstrip('.') or 'bin'),metadata={'role':item['role'],'owner':item['repository']})
 # Already-authored records keep their IDs and typed content. Rebase pinned record
 # references into this destination; implementation payloads remain unopened.
 authored={inputs[t['inputId']]['path']:t for t in state['tasks'] if t['adapter']=='study-record' and not t.get('blockedReason')};imported={};imported_ids={}
 def import_record(path):
  if path in imported:return imported[path]
  task=authored[path];original=task['data'];item=inputs[task['inputId']];ptr=pointer(task);key=(original['kind'],original['id'])
  if key in imported_ids:imported[path]=imported_ids[key];return imported[path]
  def rebase(value,selector=''):
   if isinstance(value,dict):
    if set(value)=={'kind','id','version','path','sha256'}:return import_record(value['path'])
    if set(value)=={'repository','revision','path','sha256','selector'}:return run.pointer(item,selector)
    if value.get('status')=='present' and set(value)=={'status','value','provenance'}:return present(rebase(value['value'],selector+'/value'),run.pointer(item,selector+'/value'))
    return {k:rebase(v,selector+'/'+escape(k)) for k,v in value.items()}
   if isinstance(value,list):return [rebase(v,selector+'/'+str(i)) for i,v in enumerate(value)]
   return value
  data=rebase({k:v for k,v in original.items() if k not in ('schema','kind','id','version','origin')});native_ref=w.refs['artifact','input:'+task['inputId']]
  if original['kind']=='contract':data['native'].append(native_ref)
  elif original['kind']=='approach':data['native']=native_ref
  elif original['kind']=='artifact':
   data['nativeMetadata']=present({'authoredMetadata':data['nativeMetadata'],'sourceRecord':native_ref},ptr)
   if original['file']['status']=='present':
    data['file']=missing('Source payload deliberately remains outside the migration; pinned author locator retained')
    data['externalLocator']=present({'repository':'gamma',**original['file']['value'],'binding':'Author-declared bytes and hash; not opened or executed by migration'},ptr)
  reference=w.put(original['kind'],original['id'],ptr,**data);imported[path]=reference;imported_ids[key]=reference
  p=problem(task,type='coding')
  p[{'contract':'contracts','approach':'approaches','artifact':'artifacts'}[original['kind']]].append(reference)
  return reference
 for task in state['tasks']:
  if task['adapter']!='study-record':continue
  if task.get('blockedReason'):
   converted_rows.append({'inputId':task['inputId'],'selector':task['selector'],'status':'blocked','reason':task['blockedReason']});continue
  import_record(inputs[task['inputId']]['path']);converted_rows.append({'inputId':task['inputId'],'selector':task['selector'],'status':'converted','problemId':task['problemId']})
 for pid,p in sorted(problems.items()):
  origin=p.pop('origin')
  for key in ('contracts','approaches','artifacts','evidence','sources','companyReports','relationships'):
   unique={x['id']:x for x in p[key]};p[key]=[unique[k] for k in sorted(unique)]
  w.put('problem',pid,origin,**p)
 result={'schema':'study.conversion.v1','records':sorted(w.refs.values(),key=lambda r:(r['kind'],r['id'])),'rows':converted_rows,'counts':dict(Counter(r['kind'] for r in w.refs.values())),'historicalQualificationPromotions':0,'consumerChanges':0}
 run.checkpoint('convert',result);return result


def load_records(run):
 refs=run.phase('convert')['records'];records={}
 for r in refs:
  p=within(run.dest,run.dest/r['path']);raw=p.read_bytes()
  if sha(raw)!=r['sha256']:raise ValueError('Immutable record hash mismatch: '+r['path'])
  value=decode(raw)
  if (value['kind'],value['id'],value['version'])!=(r['kind'],r['id'],r['version']):raise ValueError('Reference identity/version mismatch')
  records[(r['kind'],r['id'])]=(r,value)
 return records


def validate(run,args):
 from jsonschema import Draft202012Validator
 Draft202012Validator.check_schema(SCHEMA);validator=Draft202012Validator(SCHEMA);records=load_records(run);errors=[];reference_count=0;graph_count=0;reference_cache={};pointer_cache={}
 source_items={(x['repository'],x['path'],x['sha256']):x for x in run.phase('inventory')['items'] if x['sha256']}
 def resolve_ref(r):
  nonlocal reference_count
  reference_count+=1;cache_key=(r['path'],r['sha256'])
  if cache_key in reference_cache:return reference_cache[cache_key]
  raw=within(run.dest,run.dest/r['path']).read_bytes()
  if sha(raw)!=r['sha256']:raise ValueError('Reference hash mismatch: '+r['path'])
  value=decode(raw)
  if (value['kind'],value['id'],value['version'])!=(r['kind'],r['id'],r['version']):raise ValueError('Reference identity/version mismatch: '+r['path'])
  reference_cache[cache_key]=value;return value
 def walk(value):
  if isinstance(value,dict):
   if set(value)=={'kind','id','version','path','sha256'}:resolve_ref(value)
   if set(value)=={'path','sha256','bytes','mediaType'}:
    raw=within(run.dest,run.dest/value['path']).read_bytes()
    if sha(raw)!=value['sha256'] or len(raw)!=value['bytes']:raise ValueError('Blob integrity mismatch: '+value['path'])
   if set(value)=={'repository','revision','path','sha256','selector'}:
    pointer_key=(value['repository'],value['path'],value['sha256'])
    if pointer_key not in pointer_cache:
     if value['repository']=='migration-inventory':raw=within(run.dest,run.dest/value['path']).read_bytes()
     elif pointer_key in source_items:raw=run.snapshot(source_items[pointer_key])
     else:
      # Unchanged records may retain their older immutable source snapshot.
      candidates=list((run.dest/'source-cache'/value['repository']).glob(value['sha256']+'.*'))
      if len(candidates)!=1:raise ValueError('Missing source provenance snapshot')
      raw=candidates[0].read_bytes()
     if sha(raw)!=value['sha256']:raise ValueError('Source provenance hash mismatch')
     try:parsed=decode(raw)
     except (ValueError,UnicodeDecodeError):parsed=None
     pointer_cache[pointer_key]=parsed
    selector=value['selector']
    if selector and pointer_cache[pointer_key] is not None:
     current=pointer_cache[pointer_key]
     for part in selector.lstrip('/').split('/'):
      part=part.replace('~1','/').replace('~0','~');current=current[int(part)] if isinstance(current,list) else current[part]
   for child in value.values():walk(child)
  elif isinstance(value,list):
   for child in value:walk(child)
 graphdefs={'simulatte.architecture.v1':'ArchitectureModel','simulatte.systemDiagram.v4':'SimulationDiagramV4','simulatte.systemDiagram.v5':'SimulationDiagramV5','simulatte.composableStudy.v2':'ComposableStudyDocument','simulatte.composableStudy.graph.v2':'Study_graph'}
 for key,(r,value) in records.items():
  try:
   record_schema={**SCHEMA,'oneOf':[{'$ref':'#/$defs/'+value['kind'].title().replace('-','')}]};Draft202012Validator(record_schema).validate(value);walk(value)
   if value['kind']=='company-report':
    if resolve_ref(value['company'])['kind']!='company' or resolve_ref(value['contract'])['kind']!='contract' or resolve_ref(value['source'])['kind']!='source':raise ValueError('Company report has incompatible reference types')
   if value['kind']=='approach':
    if resolve_ref(value['contract'])['kind']!='contract':raise ValueError('Approach contract reference has the wrong kind')
    stages=value['stages']
    if len({s['id'] for s in stages})!=len(stages):raise ValueError('Duplicate stage identity')
    if value['sequenceStatus']=='study-ready' and len(stages)<8:raise ValueError('Study-ready approach requires at least eight stages')
    for stage in stages:
     for c in stage['checks']:
      record=resolve_ref(c)
      if record['kind']!='artifact' or record['type']!='check':raise ValueError('Stage check does not resolve to a check artifact')
   if value['kind']=='artifact' and value['file']['status']=='present' and value.get('documentSchema') in graphdefs:
    blob=value['file']['value'];native=decode((run.dest/blob['path']).read_bytes());gvalidator=Draft202012Validator({**SCHEMA,'oneOf':[{'$ref':'#/$defs/'+graphdefs[value['documentSchema']]}]});gvalidator.validate(native);graph_count+=1
  except Exception as e:errors.append({'record':r['id'],'path':r['path'],'error':str(e)[:900]})
 # Check semantic graph replay using the pinned Simulatte implementation, not a
 # new interpretation of insert/expand/merge or an invented JSON Patch adapter.
 inv=run.phase('inventory');native_root=run.dest/'native-lucyd'/'public'
 for item in inv['items']:
  if item['repository']=='simulatte' and item['snapshot']:
   p=within(native_root,native_root/str(Path(item['path']).relative_to('public')));p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(run.snapshot(item))
 if (native_root/'data/system-diagram/problems.json').exists():
  output=run.dest/'lucyd-validation.json';process=subprocess.run(['node',str(run.dest/run.toolchain['lucyd-bridge.cjs']['snapshot']),str(native_root),str(output)],capture_output=True,text=True)
  if process.returncode:
   details=read(output) if output.exists() else {'stderr':process.stderr[-1500:]};errors.append({'scope':'Lucyd native validation/replay','error':details})
  lucyd=read(output) if output.exists() else None
 else:lucyd=None
 result={'schema':'study.validation.v1','records':len(records),'referencesChecked':reference_count,'centralGraphSchemasChecked':graph_count,'lucyd':lucyd,'errors':errors,'passed':not errors,'candidateExecutions':0,'qualificationPromotions':0};run.checkpoint('validate',result)
 if errors:raise ValueError(f'Validation failed for {len(errors)} records/boundaries; inspect validate.json')
 return result


def build_catalogue(run,args):
 if not run.phase('validate')['passed']:raise ValueError('Validate before building discovery')
 records=load_records(run);entries=[];companies=defaultdict(list);missing_counts=Counter()
 for (kind,id),(reference,p) in records.items():
  if kind!='problem':continue
  counts=Counter();gaps=[];stages=[]
  for r in p['artifacts']:
   a=records[r['kind'],r['id']][1]
   if a['type']=='implementation':counts[a['language'] or 'unknown']+=1
  for r in p['approaches']:
   a=records[r['kind'],r['id']][1];stages.append({'approach':r,'representation':a['representation'],'stages':len(a['stages'])})
   for field_name in ('explanation','chooseWhen','tradeoffs','hints'):
    if a[field_name]['status']!='present':gaps.append(a['id']+':'+field_name+':'+a[field_name]['status'])
  contracts=[records[r['kind'],r['id']][1] for r in p['contracts']]
  if not any(c['statement']['status']=='present' and c['contentScope'] in ('full-statement','authored') for c in contracts):gaps.append('complete-statement')
  if p['type']=='coding':
   for language in ('javascript','python'):
    if not counts[language]:gaps.append(language+'-implementation-not-located')
  if not p['approaches']:gaps.append('authored-approach-not-located')
  if p['identity']['status']=='unresolved':gaps.append('official-identity-unresolved')
  for gap in gaps:missing_counts[gap.split(':')[-1]]+=1
  company_names=[]
  for r in p['companyReports']:
   report=records[r['kind'],r['id']][1];company=records['company',report['company']['id']][1];company_names.append(company['name']);companies[company['id']].append({'problem':reference,'report':r})
  entries.append({'problem':reference,'title':p['title'],'type':p['type'],'topics':p['topics'],'companies':sorted(set(company_names)),'contracts':p['contracts'],'implementationCounts':dict(counts),'approaches':stages,'missing':gaps,'historicalEvidenceCount':len(p['evidence']),'admissionStatus':'not-established-by-migration'})
 result={'schema':'study.discovery.v1','entries':sorted(entries,key=lambda x:x['problem']['id']),'counts':{'problems':len(entries),'types':dict(Counter(e['type'] for e in entries)),'namespaces':dict(Counter(e['problem']['id'].split(':',1)[0] for e in entries))}}
 write(run.dest/'generated/discovery.json',result);write(run.dest/'generated/company-index.json',{'schema':'study.company-index.v1','companies':dict(sorted(companies.items()))});write(run.dest/'generated/completeness.json',{'schema':'study.completeness.v1','counts':dict(missing_counts),'entries':[{'problem':e['problem'],'missing':e['missing']} for e in entries]});write(run.dest/'generated/relationship-candidates.json',{'schema':'study.relationship-candidates.v1','candidates':run.phase('resolve-identities')['proposedRelationships'],'automaticMerges':0});run.checkpoint('build-catalogue',result['counts']);return result['counts']


def embedding_inputs(run):
 """Separate purposes; only already-opened eligible migration content is used."""
 records=load_records(run);rows=[]
 def add(owner,purpose,name,text):
  if not isinstance(text,str) or not text.strip():return
  # Explicit deterministic character chunker; no implied tokenizer equivalence.
  for ordinal,start in enumerate(range(0,len(text),1100)):
   chunk=text[start:start+1200]
   rows.append({'id':owner['id']+':'+purpose+':'+name+':'+str(ordinal),'purpose':purpose,'owner':owner,'field':name,'chunkOrdinal':ordinal,'text':chunk,'textSha256':sha(chunk.encode())})
   if start+1200>=len(text):break
 for (kind,id),(r,value) in records.items():
  if kind=='contract' and value['statement']['status']=='present':
   # Previews are discovery material, not a full-spec recognition claim.
   add(r,'problem-discovery','statement-'+value['contentScope'],value['statement']['value'])
   for name in ('requirements','constraints'):
    if value[name]['status']=='present':add(r,'problem-discovery',name,json.dumps(value[name]['value'],ensure_ascii=False,sort_keys=True))
  elif kind=='approach':
   if value['explanation']['status']=='present':add(r,'solution-study','explanation',value['explanation']['value'])
   for stage in value['stages']:
    if stage['explanation']['status']=='present':add(r,'solution-study',stage['id']+':explanation',stage['explanation']['value'])
  elif kind=='artifact' and value['type'] in ('diagram','api-contract','pseudocode'):
   add(r,'artifact-search','title',value['title'])
 return sorted(rows,key=lambda x:x['id'])


def build_embeddings(run,args):
 rows=embedding_inputs(run);result=embeddings.build(run.dest,rows,Path(args.encoder_contract) if args.encoder_contract else None,Path(args.embedding_baseline) if args.embedding_baseline else None)
 run.checkpoint('build-embeddings',result);return result


def reconcile(run,args):
 inventory=run.phase('inventory');extraction=run.phase('extract');conversion=run.phase('convert');validation=run.phase('validate');source_rows={(t['inputId'],t['selector']) for t in extraction['tasks']};output_rows={(t['inputId'],t['selector']) for t in conversion['rows']};missing_rows=sorted(source_rows-output_rows);dispositions={x['inputId']:x for x in extraction['dispositions']};unaccounted=[x['id'] for x in inventory['items'] if x['id'] not in dispositions];changed=[]
 for item in inventory['items']:
  if item['snapshot'] is None:continue
  root=run.config['roots'][item['repository']]
  if item['path']=='explicit-private-catalogue.json':p=Path(run.config['gammaCatalogue'])
  elif item['path']=='explicit-private-session.json':p=Path(run.config['meshSession'])
  else:p=Path(root,item['path'])
  if not p.exists() or sha(p.read_bytes())!=item['sha256']:changed.append(item['id'])
 # Newly arriving source files are detected without reading their contents.
 known={i['path'] for i in inventory['items'] if i['role']=='gamma-source'};current={str(p.relative_to(run.config['roots']['gamma'])) for p in source_files(run.config['roots']['gamma'])}
 known_metadata={i['path'] for i in inventory['items'] if i['role'] in ('hack-worklist','gamma-source-metadata','gamma-paired-manifest','gamma-study-record')};current_metadata={str(p.relative_to(run.config['roots']['gamma'])) for p,role in source_metadata_files(run.config['roots']['gamma'])}
 metadata_changed=[]
 for item in inventory['items']:
  if item['role']=='gamma-source':
   source=Path(run.config['roots']['gamma'],item['path'])
   if source.is_file() and (source.stat().st_size!=item['bytes'] or item.get('mtimeNs') and str(source.stat().st_mtime_ns)!=item['mtimeNs']):metadata_changed.append(item['id'])
 result={'schema':'study.reconciliation.v1','inventoryFiles':len(inventory['items']),'extractedRows':len(source_rows),'accountedRows':len(output_rows),'unaccountedInputs':unaccounted,'missingOutputRows':missing_rows,'dispositions':dict(Counter(x['status'] for x in extraction['dispositions'])),'recordCounts':conversion['counts'],'changedSinceSnapshot':changed,'newGammaSourceFilesSinceSnapshot':sorted(current-known),'removedGammaSourceFilesSinceSnapshot':sorted(known-current),'snapshotFaithfullyMigrated':not missing_rows and not unaccounted and validation['passed'],'changedGammaSourceMetadataSinceSnapshot':metadata_changed,'sourceCaughtUp':not changed and not metadata_changed and not current-known and not known-current,'consumerSwitchApproved':False,'qualificationPromotions':0,'embeddings':run.phase('build-embeddings'),'notes':['Source-local identities remain separate until reviewed mappings exist.','Legacy evidence is preserved without upgrading qualifications.','Encrypted collections and unopened source/case payloads remain closed.','Migration success and educational completeness are different results.','New source changes require another inventory/run; they never mutate this snapshot.']}
 result.update(newGammaMetadataFilesSinceSnapshot=sorted(current_metadata-known_metadata),removedGammaMetadataFilesSinceSnapshot=sorted(known_metadata-current_metadata))
 result['blockedOutputRows']=[row for row in conversion['rows'] if row['status']=='blocked']
 result['sourceCaughtUp']=result['sourceCaughtUp'] and current_metadata==known_metadata
 run.checkpoint('reconcile',result);return result


def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=(*STAGES,'all'));parser.add_argument('--destination',required=True);parser.add_argument('--gamma');parser.add_argument('--simulatte');parser.add_argument('--hatch');parser.add_argument('--gamma-catalogue');parser.add_argument('--mesh-session');parser.add_argument('--encoder-contract');parser.add_argument('--embedding-baseline');args=parser.parse_args(argv);run=Run(args.destination)
 functions={'inventory':inventory,'extract':extract,'resolve-identities':resolve,'convert':convert,'validate':validate,'build-catalogue':build_catalogue,'build-embeddings':build_embeddings,'reconcile':reconcile}
 import fcntl
 with (run.dest/'.migration.lock').open('a') as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise ValueError('Another migration owns this destination')
  for name in STAGES if args.stage=='all' else (args.stage,):
   result=functions[name](run,args);counts={k:v for k,v in result.items() if isinstance(v,(str,int,bool)) or k in ('counts','recordCounts') or k=='dispositions' and isinstance(v,dict)};print(json.dumps({'stage':name,**counts},sort_keys=True),flush=True)

if __name__=='__main__':main()
