"""Independent verifier for the sanitized exact-source guidance release."""
from pathlib import Path
import ast,hashlib,json,math,statistics,struct,subprocess
D=Path(__file__).resolve().parent;P=D
load=lambda p:json.loads(p.read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
a=load(P/'guide-assets.json');receipts=load(P/'qualification-receipts.json')['source_hashes'];n=0;jss=set();pys=set();seenfiles=set()
for profile in a['profiles']:
 base=P/'profiles'/profile['id'];raw=(base/'dictionary.bin').read_bytes();assert raw[:4]==b'LTD1';count=int.from_bytes(raw[4:8]);at=8;v=[]
 for _ in range(count):
  length=int.from_bytes(raw[at:at+4]);at+=4;v.append(raw[at:at+length].decode());at+=length
 assert at==len(raw) and v==profile['literals']==load(base/'dictionary.json');assert sha(raw)==profile['dictionary_sha256'];width=profile['width'];counts=[];packetbytes=0;chars=0
 for g in profile['guides']:
  packet=(P/g['packet_reference']).read_bytes();assert packet[:4]==b'LTV1' and packet[4]==width and packet[5:37].hex()==sha(raw);k=int.from_bytes(packet[37:41]);bits=''.join(f'{byte:08b}' for byte in packet[41:]);assert len(packet)==41+math.ceil(k*width/8);assert not any(c=='1' for c in bits[k*width:])
  ids=[int(bits[i*width:(i+1)*width],2) for i in range(k)];assert ids==g['sequence'] and all(i<len(v) for i in ids)
  source=''.join(v[i] for i in ids);assert source==g['source'] and source.encode()==(P/g['source_reference']).read_bytes();assert sha(source.encode())==g['source_sha256'];assert sha(packet)==g['packet_sha256'];assert g['source_sha256']in receipts and receipts[g['source_sha256']]['passed']
  # Forward shortest-path oracle, independent of export's backward substitution parser.
  best=[10**9]*(len(source)+1);best[0]=0
  for pos in range(len(source)):
   if best[pos]==10**9:continue
   for s in v:
    if source.startswith(s,pos):best[pos+len(s)]=min(best[pos+len(s)],best[pos]+1)
  assert best[-1]==k,(profile['id'],g['problem_id'],'nonminimal parse')
  if profile['language']=='python':ast.parse(source);pys.add(g['source_sha256'])
  else:jss.add(source)
  seenfiles.add(g['source_reference']);counts.append(k);packetbytes+=len(packet);chars+=sum(len(v[i])==1 for i in ids);n+=1
 m=profile['metrics'];assert m['selections']==sum(counts) and m['median_selections']==statistics.median(counts) and m['p95_selections']==sorted(counts)[math.ceil(.95*len(counts))-1];assert m['packet_bytes']==packetbytes and m['dictionary_bytes']==len(raw) and m['package_bytes']==len(raw)+packetbytes;assert m['single_character_selections']==chars and m['whole_solution_entries']==0
script="const fs=require('node:fs'),vm=require('node:vm');for(const s of JSON.parse(fs.readFileSync(0,'utf8')))new vm.Script(s);"
r=subprocess.run(['node','-e',script],input=json.dumps(sorted(jss)),text=True,capture_output=True,timeout=30);assert r.returncode==0,r.stderr
assert len(seenfiles)==len(list((P/'sources').rglob('*.js')))+len(list((P/'sources').rglob('*.py')))
for rel,h in a['notices'].items():assert sha((P/rel).read_bytes())==h
for f in P.rglob('*'):
 if f.is_file() and f.suffix not in ['.bin','.ltv']:
  text=f.read_text();assert ('/'+'home'+'/') not in text and ('/'+'Users'+'/') not in text,(f,'private path')
result={'passed':True,'packets_decoded':n,'minimum_parses_checked':n,'unique_source_files':len(seenfiles),'javascript_sources_syntax_checked':len(jss),'python_sources_syntax_checked':len(pys),'native_source_execution':False,'new_source_qualification':False,'notices_verified':len(a['notices']),'public_tree_private_path_scan':'passed','source_dictionary_packet_and_metrics_verified':True}
(D/'verification-rerun.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
