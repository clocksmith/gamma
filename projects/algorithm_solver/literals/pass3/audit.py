"""Audit all retained packet bytes against qualified source identities and costs."""
import argparse, hashlib, json, sys
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--pilot',type=Path,required=True);p.add_argument('--run',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 sys.path[:0]=[str(a.pilot),str(a.pilot/'pass2/working')]
 from literals import dictionary_bytes
 from bitpack import decode,encode
 sha=lambda b:hashlib.sha256(b).hexdigest()
 q=json.loads((a.run/'qualification-v1/report.json').read_text());qualified={(r['problem'],r['source_sha256']) for r in q['rows'] if r['passed']}
 m=json.loads((a.run/'generated/manifest.json').read_text());n=0;sets=0
 for sweep in ['search-v1','search-v2']:
  summary=json.loads((a.run/sweep/'summary.json').read_text())
  for trial in summary['trials']:
   folder=a.run/sweep;data=json.loads((folder/'encodings'/f"{trial['id']}.json").read_text());literals=data['literals'];dictionary=dictionary_bytes(literals)
   assert len(dictionary)==trial['metrics']['dictionary_bytes']
   for key,row in data['programs'].items():
    source=(a.run/'generated'/m['variants'][key][row['variant']]['file']).read_text()
    assert ''.join(literals[i] for i in row['sequence'])==source
    assert sha(source.encode())==row['source_sha256'] and (key,row['source_sha256']) in qualified
   for cost in trial['costs']:
    if not cost['feasible']:continue
    location=folder/'packets'/trial['id']/str(cost['budget']);assert (location/'dictionary.ltd').read_bytes()==dictionary
    size=0;bits=0;padding=0
    for key,row in data['programs'].items():
     packet=(location/(key+'.ltv')).read_bytes();assert packet==encode(literals,row['sequence'],cost['width']);assert sha(decode(dictionary,packet).encode())==row['source_sha256'];n+=1;size+=len(packet);bits+=cost['width']*len(row['sequence']);padding+=(-cost['width']*len(row['sequence']))%8
    assert size==cost['packet_bytes'] and bits==cost['selection_bits'] and padding==cost['padding_bits'] and size+len(dictionary)==cost['total_package_bytes'];sets+=1
 summary={'schema':'gamma.literal-pass3-audit.v1','packets_verified':n,'dictionary_budget_sets_verified':sets,'qualified_sources':len(qualified),'native_checks_passed':q['checks_passed'],'native_checks_total':q['checks_total'],'qualification_sha256':sha((a.run/'qualification-v1/report.json').read_bytes()),'audit_sha256':sha(Path(__file__).read_bytes()),'evidence':'Exact reconstructed bytes match sources already executed in qualification-v1; this audit does not rerun execution.'}
 a.output.write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
