"""Fixed-codebook fraction diagnostic; no fitting, source changes or promotion."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import time
import ratio
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'cost-decomposition-v1'));import analyze

def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

tail=module('fraction_tail',LIT/'tail-search-v1/search.py')
segment=module('fraction_segment',LIT/'segmentation-audit-v1/segment.py')
POLICIES=('canonical','min_char','min_fraction')


def main(work,out):
    c=json.loads((HERE/'contract.json').read_text())
    for rel,h in c['code_hashes'].items():assert analyze.sha((LIT/rel).read_bytes())==h,rel
    for rel,h in c['private_files'].items():assert analyze.sha((work/rel).read_bytes())==h,rel
    old={(a['arm'],a['width']):a for a in json.loads((LIT/'binding-descent-v1/evidence/results.json').read_text())['arms']}
    out.mkdir(parents=True,exist_ok=False);started=time.monotonic();results=[];certificates=[]
    for seed in c['seeds']:
        root=work/seed['relative_path'];prior=old[seed['arm'],seed['width']]
        texts=json.loads((root/'sources.json').read_text());vocab=json.loads((root/'dictionary.json').read_text());db=analyze.dictionary_bytes(vocab)
        expected={str(i) for group in c['partition'].values() for i in group}
        assert set(texts)==set(prior['qualification'])==expected and all(q['passed'] for q in prior['qualification'].values())
        assert not prior['illegal_entry_sha256'] and len(vocab)<=2**seed['width']
        for pid,text in texts.items():assert text.isascii() and analyze.sha(text.encode())==prior['per_problem'][pid]['source_sha256']
        fraction={}
        for split,key in [('fit','dev_fit'),('validation','dev_val')]:
            subset={str(pid):texts[str(pid)] for pid in c['partition'][key]}
            seq,info=ratio.solve(subset,vocab,c['max_iterations']);proof=ratio.certificate(subset,vocab,info['p'],info['q'])
            assert sum(x['minimum_transformed_cost'] for x in proof.values())==0
            assert sum(x['minimum_selections_at_cost'] for x in proof.values())==info['selections']
            assert all(sum((info['q']*int(len(vocab[i])==1)-info['p']) for i in seq[pid])==proof[pid]['minimum_transformed_cost'] for pid in subset)
            cert={'seed':seed['name'],'split':split,**info,'per_problem':proof,'independent_minimum_sum':0}
            certificates.append(cert);fraction.update(seq)
            analyze.write(out/f'{seed["name"]}-{split}-certificate.json',cert)
        for policy in POLICIES:
            rows={};sequences={};packets=out/f'{seed["name"]}-{policy}';packets.mkdir();(packets/'dictionary.bin').write_bytes(db)
            for pid,text in sorted(texts.items()):
                seq=fraction[pid] if policy=='min_fraction' else segment.encode(text,vocab,policy)
                packet=analyze.encode(vocab,seq,seed['width']);assert analyze.decode(db,packet)==text
                chars,n=ratio.counts(vocab,seq)
                if policy=='canonical':
                    assert seq==analyze.shortest_encode(text,vocab) and n==prior['per_problem'][pid]['selections']
                    assert chars==prior['per_problem'][pid]['single_characters']
                rows[pid]={'encodable':True,'source_sha256':analyze.sha(text.encode()),'source_bytes':len(text.encode()),
                           'selections':n,'actions':n+1,'single_characters':chars,'packet_bytes':len(packet),
                           'packet_sha256':analyze.sha(packet),'qualification_reused':True}
                sequences[pid]=seq;(packets/f'{pid}.bin').write_bytes(packet)
            analyze.write(packets/'sequences.json',sequences)
            a={'seed':seed['name'],'policy':policy,'width':seed['width'],'dictionary_sha256':analyze.sha((root/'dictionary.json').read_bytes()),
               'dictionary_bytes':len(db),'per_problem':rows,'qualification_receipt_sha256':c['historical_evidence_sha256']}
            for split,key in [('fit','dev_fit'),('validation','dev_val')]:
                ids=c['partition'][key];d=tail.aggregate(rows,ids,len(db));subset=[rows[str(i)] for i in ids]
                d.update(single_character_codes=sum(x['single_characters'] for x in subset),qualified=len(ids),
                         source_bytes=sum(x['source_bytes'] for x in subset),framing_bytes=41*len(ids),
                         payload_bits=seed['width']*d['selections']['total'],
                         padding_bits=sum(8*(x['packet_bytes']-41)-seed['width']*x['selections'] for x in subset),
                         package_with_decoder_dependencies=d['package_bytes']+c['decoder_dependency_bytes'])
                a[split]=d
            results.append(a)
    analyze.write(out/'results.json',{'schema':'gamma.fraction-certificate.v1','arms':results,'certificates':certificates,
        'contract_sha256':analyze.sha((HERE/'contract.json').read_bytes()),'seconds':time.monotonic()-started,
        'decodes':sum(len(a['per_problem']) for a in results)})
    print(json.dumps({'complete':True,'decodes':sum(len(a['per_problem']) for a in results),'seconds':time.monotonic()-started}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();main(a.work,a.output)
