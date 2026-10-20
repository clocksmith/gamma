"""Package measured flat literal dictionaries into real 4..8-bit selections."""
import argparse,json,sys
from pathlib import Path
from bitpack import encode,decode,dictionary_bytes
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[1]))
from literals import digest,json_bytes

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 args.output.mkdir(parents=True,exist_ok=False)
 configurations=[('whole5','b38bacac0ae8196b401e',5),('characters6','e642cf0841d62fe87518',6),('shared7','08abe4c1a83270125a3a',7),('compact8','fdd94e86cfb2e1ed4f07',8),('baseline7','e53a4deb8baf95ffc2ba',7),('baseline8','f4b70f1e7083ca6f960d',8)]
 summaries=[]
 for name,identity,bits in configurations:
  raw=(ROOT.parent/'results/encodings'/f'{identity}.json').read_bytes();source=json.loads(raw)
  output=args.output/name;output.mkdir();(output/'programs').mkdir();(output/'assembled').mkdir()
  dictionary=dictionary_bytes(source['literals']);(output/'dictionary.ltd').write_bytes(dictionary)
  (output/'dictionary.json').write_bytes(json_bytes({'literals':[{'id':i,'text':v,'utf8_bytes':len(v.encode())} for i,v in enumerate(source['literals'])]}))
  rows={}
  for key,row in source['programs'].items():
   packet=encode(source['literals'],row['sequence'],bits);text=decode(dictionary,packet)
   if digest(text.encode())!=row['source_sha256']:raise ValueError('source reconstruction drift')
   (output/'programs'/f'{key}.ltv').write_bytes(packet);(output/'assembled'/f'{key}.js').write_bytes(text.encode())
   rows[key]={'sequence':row['sequence'],'selections':len(row['sequence']),'selection_bits':bits*len(row['sequence']),'padding_bits':(-bits*len(row['sequence']))%8,'packet_bytes':len(packet),'packet_sha256':digest(packet),'source_sha256':row['source_sha256'],'variant':source['selection']['choices'][key]}
  result={'schema':'gamma.working-literal-language.v1','name':name,'bits_per_selection':bits,'entry_budget':1<<bits,'literal_count':len(source['literals']),'dictionary_bytes':len(dictionary),'dictionary_sha256':digest(dictionary),'source_encoding_id':identity,'source_encoding_sha256':digest(raw),'programs':rows,'coverage':len(rows),'total_selections':sum(r['selections'] for r in rows.values()),'selection_bits':sum(r['selection_bits'] for r in rows.values()),'padding_bits':sum(r['padding_bits'] for r in rows.values()),'framing_bytes':41*len(rows),'packet_bytes':sum(r['packet_bytes'] for r in rows.values()),'cross_program_literals':source['metrics']['cross_program_literals'],'cross_program_selections':source['metrics']['cross_program_selections'],'whole_program_literals':sum(any(v==decode(dictionary,encode(source['literals'],r['sequence'],bits)) for r in source['programs'].values()) for v in source['literals'])}
  result['total_package_bytes']=result['dictionary_bytes']+result['packet_bytes']
  (output/'manifest.json').write_bytes(json_bytes(result));summaries.append({k:v for k,v in result.items() if k!='programs'})
 (args.output/'summary.json').write_bytes(json_bytes({'languages':summaries,'budget_notes':{'16':'Historical bounded search covered16/20; no complete substantial-sharing result measured.','32':'Twenty whole-program entries fit as a diagnostic baseline; no substantial-sharing language selected at this budget.','64':'Complete character language:61 literals,6bits.','128':'Complete shared helper/line language:79 literals,7bits.','256':'Complete compact dictionary language:140 literals,8bits.'}}))
 print(json.dumps(summaries))
if __name__=='__main__':main()
