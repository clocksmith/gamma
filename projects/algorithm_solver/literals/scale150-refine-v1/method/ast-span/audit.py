import json,hashlib,importlib.util,statistics,math
from pathlib import Path
C=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location('qualified150',C/'load_sources.py');data=importlib.util.module_from_spec(spec);spec.loader.exec_module(data);ss=data.expanded;audit=data.audit;sha=data.sha
contract=json.loads((C/'contract.json').read_text());summary=json.loads((C/'summary.json').read_text());packets=0;counts=[]
for p,h in contract['code_hashes'].items():assert sha(Path(p).read_bytes())==h
for r in summary['records']:
 p=C/'measurement'/r['label'];v=json.loads((p/'dictionary.json').read_text());raw=(p/'dictionary.ltd').read_bytes();m=json.loads((p/'manifest.json').read_text());score,selected=audit.score(ss,v,r['width']);assert len(v)<=2**r['width'] and not set(v)&data.banned
 for k in ['selections','dictionary_bytes','packet_bytes','package_bytes']:assert score[k]==r['metrics'][k]
 seqcounts=[];chars=0
 for row in m['programs']:
  decoded,words,seq,w=audit.packet_audit.unpack(raw,(p/f"{row['id']}.ltv").read_bytes());assert words==v and seq==row['sequence'] and w==r['width'];assert decoded==ss[row['id']][row['variant']];assert sha(decoded.encode())==row['source_sha256'];assert selected[row['id']]==(row['variant'],len(seq));packets+=1;seqcounts.append(len(seq));chars+=sum(len(v[i])==1 for i in seq)
 assert len(seqcounts)==150 and sum(seqcounts)==r['all150']['selections'];assert statistics.median(seqcounts)==r['all150']['median'] and sorted(seqcounts)[math.ceil(.95*150)-1]==r['all150']['p95'];assert chars/sum(seqcounts)==r['all150']['character_fraction']
 for f in v:
  if len(f)>1:assert sum(any(f in t for t in variants.values()) for variants in ss.values())>=2
 counts.append({'label':r['label'],'entries':len(v),'packets':len(seqcounts),'whole_program_literals':0,'minimum_distinct_problem_support':2})
assert packets==900
traces=[]
for n in [128,256]:
 t=json.loads((C/f'measurement/trace-{n}.json').read_text());rank=sum(len(r['candidates']) for r in t['rankings']);assert t['trials']<=2400 and rank<=768;traces.append({'entries_cap':n,'legal_trials':t['trials'],'ranking_probes':rank,'elapsed_seconds':t['elapsed_seconds'],'stop':t['stop'],'accepted_moves':sum(bool(r['accepted']) for r in t['rounds'])})
result={'passed':True,'packets_independently_decoded':packets,'source_choices_independently_minimized':packets,'source_alternatives':1006,'native_qualification_unchanged':True,'qualified_stage_audit_sha256':sha((data.D/'independent-audit.json').read_bytes()),'summary_sha256':sha((C/'summary.json').read_bytes()),'contract_sha256':sha((C/'contract.json').read_bytes()),'audit_code_sha256':sha(Path(__file__).read_bytes()),'records':counts,'search':traces,'artifact_bytes':sum(p.stat().st_size for p in C.rglob('*') if p.is_file())};assert result['artifact_bytes']<256*1024**2
(C/'independent-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
