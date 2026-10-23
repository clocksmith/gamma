"""Fixed artifacts only: no source/dictionary fitting and no new case execution."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import time
import segment
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'cost-decomposition-v1'));import analyze
spec=importlib.util.spec_from_file_location('seg_audit_tail',LIT/'tail-search-v1/search.py');tail=importlib.util.module_from_spec(spec);spec.loader.exec_module(tail)
POLICIES=('canonical','shortest_min_char','shortest_max_char','min_char')


def main(work,out):
    c=json.loads((HERE/'contract.json').read_text())
    for rel,h in c['code_hashes'].items():assert analyze.sha((LIT/rel).read_bytes())==h,rel
    for rel,h in c['private_files'].items():assert analyze.sha((work/rel).read_bytes())==h,rel
    historical=json.loads((LIT/'binding-descent-v1/evidence/results.json').read_text())
    old={(a['arm'],a['width']):a for a in historical['arms']}
    out.mkdir(parents=True,exist_ok=False);results=[];started=time.monotonic()
    for seed in c['seeds']:
        prior=old[seed['arm'],seed['width']];folder=work/seed['relative_path']
        texts=json.loads((folder/'sources.json').read_text());vocab=json.loads((folder/'dictionary.json').read_text())
        assert len(vocab)<=2**seed['width'] and not prior['illegal_entry_sha256']
        expected={str(i) for ids in c['partition'].values() for i in ids};assert set(texts)==expected
        assert set(prior['qualification'])==expected and all(q['passed'] for q in prior['qualification'].values())
        db=analyze.dictionary_bytes(vocab);allrows={}
        for policy in POLICIES:
            rows={};sequences={}
            for pid,text in sorted(texts.items()):
                assert analyze.sha(text.encode())==prior['per_problem'][pid]['source_sha256']
                seq=segment.encode(text,vocab,policy);packet=analyze.encode(vocab,seq,seed['width'])
                assert analyze.decode(db,packet)==text
                if policy=='canonical':
                    assert seq==analyze.shortest_encode(text,vocab)
                    assert len(seq)==prior['per_problem'][pid]['selections']
                    assert sum(len(vocab[i])==1 for i in seq)==prior['per_problem'][pid]['single_characters']
                rows[pid]={'encodable':True,'source_sha256':analyze.sha(text.encode()),'source_bytes':len(text.encode()),
                    'selections':len(seq),'actions':len(seq)+1,'single_characters':sum(len(vocab[i])==1 for i in seq),
                    'packet_bytes':len(packet),'packet_sha256':analyze.sha(packet),'qualification_reused':True}
                sequences[pid]=seq
            allrows[policy]=rows
            a={'seed':seed['name'],'policy':policy,'width':seed['width'],'dictionary_sha256':analyze.sha((folder/'dictionary.json').read_bytes()),
               'dictionary_bytes':len(db),'per_problem':rows,'reused_qualification_receipt':c['historical_evidence_sha256']}
            for split,key in [('fit','dev_fit'),('validation','dev_val')]:
                ids=c['partition'][key];d=tail.aggregate(rows,ids,len(db));d['single_character_codes']=sum(rows[str(i)]['single_characters'] for i in ids)
                d['package_with_decoder_dependencies']=d['package_bytes']+c['decoder_dependency_bytes'];d['qualified']=len(ids)
                d['source_bytes']=sum(rows[str(i)]['source_bytes'] for i in ids);d['framing_bytes']=41*len(ids)
                d['payload_bits']=seed['width']*d['selections']['total'];d['padding_bits']=sum(8*(rows[str(i)]['packet_bytes']-41)-seed['width']*rows[str(i)]['selections'] for i in ids)
                a[split]=d
            results.append(a);analyze.write(out/f'{seed["name"]}-{policy}-sequences.json',sequences)
        for pid in expected:
            base,lo,hi,mc=[allrows[p][pid] for p in POLICIES]
            assert lo['selections']==base['selections']==hi['selections']<=mc['selections']
            assert mc['single_characters']<=lo['single_characters']<=base['single_characters']<=hi['single_characters']
    analyze.write(out/'results.json',{'schema':'gamma.segmentation-audit.results.v1','arms':results,'seconds':time.monotonic()-started,
        'contract_sha256':analyze.sha((HERE/'contract.json').read_bytes()),'decodes':sum(len(a['per_problem']) for a in results)})
    print(json.dumps({'complete':True,'decodes':sum(len(a['per_problem']) for a in results),'seconds':time.monotonic()-started}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();main(a.work,a.output)
