"""Audit frozen source/packet provenance and physical costs without further tuning."""
import argparse,json,sys,hashlib,struct,math
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--pilot',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parent;sys.path[:0]=[str(a.pilot),str(a.pilot/'pass2/working')]
 from literals import dictionary_bytes
 from bitpack import encode,decode
 f=json.loads((root/'vocabulary-freeze.json').read_text());c=json.loads((root/'contract.json').read_text());s=json.loads((root/'search-v1/summary.json').read_text());h=json.loads((root/'heldback-expression/report.json').read_text());assert h['vocabulary_freeze_sha256']==sha((root/'vocabulary-freeze.json').read_bytes())
 for name,digest in f['implementation_sha256'].items():assert sha((root/name).read_bytes())==digest,name
 qualified={};runs=[]
 for folder in ['fit-qualification-v1','fit-input-policy-recheck','heldback-qualification']:
  report=json.loads((root/folder/'report.json').read_text());runs.append(report)
  for row in report['rows']:qualified[(row['id'],row['variant'])]=row
 assert len(qualified)==180 and all(row['passed'] for row in qualified.values())
 manifests=[json.loads((root/folder/'manifest.json').read_text()) for folder in ['fit-generated-v1','heldback-generated']];sources={}
 for folder,m in zip(['fit-generated-v1','heldback-generated'],manifests):
  for row in m['rows']:
   raw=(root/folder/row['file']).read_bytes();assert sha(raw)==row['sha256'];assert row['sha256']==qualified[(row['id'],row['variant'])]['sha256'];sources[(row['id'],row['variant'])]=raw.decode()
 packets=0
 for rec in s['trials']:
  file=root/'search-v1/encodings'/f"{rec['id']}.json";assert sha(file.read_bytes())==f['all_candidate_hashes'][rec['id']];state=json.loads(file.read_text());vocab=state['literals'];raw=dictionary_bytes(vocab);assert len(raw)==rec['metrics']['dictionary_bytes']
  for key,row in state['programs'].items():assert ''.join(vocab[i] for i in row['sequence'])==sources[(int(key),row['variant'])]
  for cost in rec['costs']:
   if not cost['feasible']:continue
   folder=root/'search-v1/packets'/rec['id']/str(cost['budget']);assert (folder/'dictionary.ltd').read_bytes()==raw;size=0
   for key,row in state['programs'].items():
    packet=(folder/(key+'.ltv')).read_bytes();assert packet==encode(vocab,row['sequence'],cost['bits_per_selection']);assert sha(decode(raw,packet).encode())==row['source_sha256'];size+=len(packet);packets+=1
   assert size==cost['packet_bytes'] and len(raw)+size==cost['total_package_bytes']
 for row in s['separate_modes']:
  raw=(root/'search-v1'/row['selector_file']).read_bytes();assert raw[:4]==b'LTS1' and struct.unpack_from('>I',raw,4)[0]==48 and len(raw)==row['selector_bytes']+row['selector_framing_bytes'];bits=[(raw[8+j//8]>>(7-j%8))&1 for j in range(48)];assert all(bit==int(i not in c['clusters'][row['cluster_order'][0]]['fit']) for i,bit in zip(row['program_order'],bits));assert row['total_package_bytes']==row['dictionary_bytes']+row['packet_bytes']+len(raw)
 held_packets=0
 for identity,result in h['results'].items():
  state=json.loads((root/'search-v1/encodings'/f'{identity}.json').read_text());vocab=state['literals'];dictionary=dictionary_bytes(vocab)
  for row in result['rows']:
   for attempt in row['attempts']:
    if not attempt['encodable']:continue
    packet=(root/'heldback-expression'/identity/attempt['packet']).read_bytes();assert sha(decode(dictionary,packet).encode())==attempt['source_sha256'];assert len(packet)==attempt['packet_bytes'];held_packets+=1
 # Supplemental strict type check on nonunique-permutation outputs in saved evidence.
 checked=0
 for file in (root/'fit-qualification-v1/observations').glob('0942-*.stdout'):
  for line in file.read_text().splitlines():
   record=json.loads(line)
   if 'result' in record:assert all(type(x) is int for x in record['result']);checked+=1
 summary={'schema':'gamma.cluster-audit.v1','qualified_source_variants':len(qualified),'qualified_problems':len({i for i,v in qualified}),'current_qualified_check_executions':sum(r['checks_total'] for r in qualified.values()),'historical_actual_check_executions_including_recheck':sum(r['checks_total'] for r in runs),'historical_failed_checks_retained':sum(r['checks_total']-r['checks_passed'] for r in runs),'fit_packets_verified':packets,'heldback_packets_verified':held_packets,'selector_packets_verified':len(s['separate_modes']),'strict_permutation_output_type_checks':checked,'dictionary_trials':s['dictionary_trials'],'vocabulary_and_procedure_hashes_unchanged':True,'audit_sha256':sha(Path(__file__).read_bytes())};a.output.write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
