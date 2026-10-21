import hashlib,importlib.util,json,time
from pathlib import Path
D=Path(__file__).resolve().parent;R=Path('/home/x/deco/gamma/output/literal-joint-v1');L=R/'projects/algorithm_solver/literals'
sha=lambda b:hashlib.sha256(b).hexdigest()
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
rw=mod('window_rw',L/'rewrite-v1/search.py');joint=rw.joint;audit=mod('window_audit',L/'joint-v1/audit.py')
c=json.loads((D/'contract.json').read_text());q=json.loads((D/'qualification/report.json').read_text());assert q['passed'] and q['checks_passed']==3*c['cases'] and q['contract_sha256']==sha((D/'contract.json').read_bytes())
for p,h in c['code_hashes'].items():assert sha(Path(p).read_bytes())==h
for p,h in c['inputs'].items():assert sha(Path(p).read_bytes())==h
began=time.monotonic();records=[];audited=0;(D/'packages').mkdir();inputs={}
for family,root,prefix in [('heap',R/'output/literal-heap-v1','full100-'),('rank',R/'output/literal-rank-v1','exact-')]:
 for width in [7,8]:
  parent=root/(prefix+str(2**width));manifest=json.loads((parent/'manifest.json').read_text());vocab=json.loads((parent/'dictionary.json').read_text());ss={};meta={}
  for p in [parent/'manifest.json',parent/'dictionary.json']:inputs[str(p)]=sha(p.read_bytes())
  for r in manifest['programs']:
   text=Path(r['source_file']).read_text();assert sha(text.encode())==r['source_sha256'];ss[r['id']]={r['variant']:text};meta[r['id'],r['variant']]={'file':r['source_file']}
  assert len(ss)==100
  baseline=joint.evaluate(ss,vocab,width)
  assert baseline['selections']==manifest['metrics']['selections'] and baseline['package_bytes']==manifest['metrics']['package_bytes']
  for phase in ['baseline','window']:
   if phase=='window':
    for r in q['rows']:
     if r['variant']=='original':continue
     text=Path(r['file']).read_text();assert sha(text.encode())==r['sha256'];ss[76][r['variant']]=text;meta[76,r['variant']]={'file':r['file']}
   state=joint.evaluate(ss,vocab,width);label=f'{family}-{2**width}-{phase}';folder=D/'packages'/label
   metrics=rw.save(folder,ss,meta,state,width,'fixed-dictionary-window-source-rewrite');m=json.loads((folder/'manifest.json').read_text());raw=(folder/'dictionary.ltd').read_bytes();total=len(raw)
   for r in m['programs']:
    packet=(folder/(str(r['id'])+'.ltv')).read_bytes();text,words,seq,w=audit.packet_audit.unpack(raw,packet);total+=len(packet)
    assert w==width and text==ss[r['id']][r['variant']] and sha(text.encode())==r['source_sha256']
    assert seq==r['sequence'] and len(seq)==audit.minimum_count(text,words);audited+=1
   assert total==metrics['package_bytes'] and metrics['whole_program_literals']==0
   target=next(r for r in m['programs'] if r['id']==76)
   row={'label':label,'metrics':metrics,'problem76':target,'dictionary_sha256':sha(raw),'manifest_sha256':sha((folder/'manifest.json').read_bytes())};records.append(row)
   print(json.dumps({'label':label,'selections':metrics['selections'],'package_bytes':metrics['package_bytes'],'problem76_selections':target['selections'],'variant':target['variant'],'median':metrics['median_selections'],'p95':metrics['p95_selections'],'character_fraction':metrics['single_character_selection_fraction']}),flush=True)
assert sum(p.stat().st_size for p in D.rglob('*') if p.is_file())<c['limits']['max_artifact_bytes']
report={'schema':'gamma.window-count.measurement.v1','records':records,'inputs':inputs,'qualification_sha256':sha((D/'qualification/report.json').read_bytes()),'code_sha256':sha(Path(__file__).read_bytes()),'packets_independently_decoded':audited,'elapsed_seconds':time.monotonic()-began,'scope':'Matched fixed dictionaries, same 100 existing development problems; only #76 receives new qualified alternatives; every helper/source byte charged. Inherited qualification of remaining 99 unchanged sources is not rerun. No dictionary search or autonomous solving.','milestone1_qualified':False,'private_artifacts':True}
(D/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
