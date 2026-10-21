import collections,hashlib,importlib.util,json,math,statistics
from pathlib import Path
D=Path(__file__).resolve().parent;L=Path('/home/x/deco/gamma/output/literal-joint-v1/projects/algorithm_solver/literals')
spec=importlib.util.spec_from_file_location('independent_window_audit',L/'joint-v1/audit.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
sha=lambda b:hashlib.sha256(b).hexdigest();rows=[]
for folder in sorted(list((D/'packages').iterdir())+list((D/'reselection/packages').iterdir())):
 m=json.loads((folder/'manifest.json').read_text());raw=(folder/'dictionary.ltd').read_bytes();counts=[];chars=0;packet_bytes=0;owners=collections.defaultdict(set)
 for r in m['programs']:
  pkt=(folder/(str(r['id'])+'.ltv')).read_bytes();text,vocab,seq,width=audit.packet_audit.unpack(raw,pkt);packet_bytes+=len(pkt);counts.append(len(seq));chars+=sum(len(vocab[x])==1 for x in seq)
  for x in set(seq):owners[x].add(r['id'])
  assert not any(v==text for v in vocab)
  assert sha(text.encode())==r['source_sha256'] and len(seq)==audit.minimum_count(text,vocab)
  assert len(pkt)==41+math.ceil(width*len(seq)/8)
 assert len(counts)==100 and len(vocab)<=2**width
 expected={'selections':sum(counts),'selection_bits':sum(counts)*width,'median_selections':statistics.median(counts),'p95_selections':sorted(counts)[94],'worst_selections':max(counts),'dictionary_bytes':len(raw),'packet_bytes':packet_bytes,'framing_bytes':4100,'package_bytes':len(raw)+packet_bytes,'single_character_selections':chars,'single_character_selection_fraction':chars/sum(counts),'cross_problem_literals':sum(len(v)>=2 for v in owners.values())}
 for k,v in expected.items():assert m['metrics'][k]==v,(folder.name,k,m['metrics'][k],v)
 rows.append({'label':str(folder.relative_to(D)),'passed':True,'programs':100,**expected})
(D/'independent-audit.json').write_text(json.dumps({'passed':True,'packages':len(rows),'programs':len(rows)*100,'rows':rows,'code_sha256':sha(Path(__file__).read_bytes())},indent=2)+'\n');print(f'{len(rows)} packages / {len(rows)*100} packets: independent costs, quantiles, exact parsing, hashes and zero whole-source entries passed')
