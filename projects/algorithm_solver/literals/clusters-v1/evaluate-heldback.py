"""Read frozen dictionaries and newly qualified heldback sources; never tune."""
import argparse,json,hashlib,sys,math,statistics
from pathlib import Path
from search import trie,encode_text
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--pilot',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parent;f=json.loads((root/'vocabulary-freeze.json').read_text());c=json.loads((root/'contract.json').read_text())
 for name,digest in f['implementation_sha256'].items():assert sha((root/name).read_bytes())==digest,name
 assert sha((root/'contract.json').read_bytes())==f['contract_sha256'];a.output.mkdir(exist_ok=False);sys.path[:0]=[str(a.pilot),str(a.pilot/'pass2/working')]
 from literals import dictionary_bytes
 from bitpack import encode,decode
 m=json.loads((root/'heldback-generated/manifest.json').read_text());q=json.loads((root/'heldback-qualification/report.json').read_text());admitted={(r['id'],r['variant']) for r in q['rows'] if r['passed']};sources={}
 for row in m['rows']:
  if row['variant']=='original':continue
  text=(root/'heldback-generated'/row['file']).read_text();assert sha(text.encode())==row['sha256'];sources.setdefault(row['id'],{})[row['variant']]=(text,(row['id'],row['variant']) in admitted)
 ids={i for cl in c['clusters'].values() for i in cl['heldback']};assert set(sources)==ids
 selected_ids=set(f['selected'].values())|set(f['union_ids'])|{i for row in f['separate_modes'] for i in row['dictionary_ids']};results={}
 for identity in sorted(selected_ids):
  src=root/'search-v1/encodings'/f'{identity}.json';assert sha(src.read_bytes())==f['all_candidate_hashes'][identity];data=json.loads(src.read_text());vocab=data['literals'];tree=trie(vocab);alphabet=set(''.join(vocab));record=data['record'];dictionary=dictionary_bytes(vocab);width=7 if len(record['problem_ids'])<48 else 8
  if len(record['problem_ids'])<48:
   target=next(cl['heldback'] for cl in c['clusters'].values() if set(cl['fit'])==set(record['problem_ids']))
  else:target=sorted(ids)
  folder=a.output/identity;folder.mkdir();rows=[]
  for i in sorted(target):
   attempts=[]
   for variant,(text,qualified) in sorted(sources[i].items()):
    try:seq=encode_text(text,tree);encodable=True
    except ValueError:seq=None;encodable=False
    attempt={'id':i,'variant':variant,'qualified':qualified,'encodable':encodable,'missing_characters':sorted(set(text)-alphabet),'source_sha256':sha(text.encode()),'selections':len(seq) if seq is not None else None}
    if seq is not None:
     raw=encode(vocab,seq,width);assert sha(decode(dictionary,raw).encode())==attempt['source_sha256'];filename=f'{i}-{variant}.ltv';(folder/filename).write_bytes(raw);attempt.update(sequence=seq,selection_bits=len(seq)*width,padding_bits=(-len(seq)*width)%8,framing_bytes=41,packet_bytes=len(raw),packet=filename)
    attempts.append(attempt)
   permitted=[x for x in attempts if x['qualified'] and x['encodable'] and (record['arm']=='joint' or x['variant']==record['arm'])]
   best=min(permitted,key=lambda x:(x['selections'],len(sources[i][x['variant']][0].encode()),x['variant'])) if permitted else None
   rows.append({'id':i,'attempts':attempts,'chosen_variant':best['variant'] if best else None,'chosen':best})
  chosen=[row['chosen'] for row in rows if row['chosen']];result={'dictionary_id':identity,'dictionary_sha256':sha(dictionary),'arm':record['arm'],'method':record['method'],'target':len(target),'qualified_expressible':len(chosen),'representation_only_expressible':sum(any(x['encodable'] and (record['arm']=='joint' or x['variant']==record['arm']) for x in row['attempts']) for row in rows),'bits_per_selection':width,'total_selections':sum(x['selections'] for x in chosen),'selection_bits':sum(x['selection_bits'] for x in chosen),'additional_packet_bytes':sum(x['packet_bytes'] for x in chosen),'dictionary_bytes_charged_on_fit_package':len(dictionary),'rows':rows};results[identity]=result
  (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 report={'schema':'gamma.cluster-heldback-expression.v1','vocabulary_freeze_sha256':sha((root/'vocabulary-freeze.json').read_bytes()),'sources':len(sources),'qualified_sources':len(admitted),'results':results,'selected':f['selected'],'scope':'Previously exposed development-heldback source expressibility only. Frozen source rewrites and dictionary IDs/bytes unchanged. No autonomous synthesis, vocabulary additions, or evaluation-driven source repair.'};(a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({key:{k:results[value][k] for k in ['qualified_expressible','target','total_selections']} for key,value in f['selected'].items()},indent=2))
if __name__=='__main__':main()
