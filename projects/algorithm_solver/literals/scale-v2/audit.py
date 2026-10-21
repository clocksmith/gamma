"""Independent receipt joins and packed-byte reconstruction; no execution claims."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import struct

ROOT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()

def unpack(dictionary,packet):
    assert dictionary[:4]==b'LTD1'
    count=struct.unpack_from('>I',dictionary,4)[0];position=8;strings=[]
    for _ in range(count):
        size=struct.unpack_from('>I',dictionary,position)[0];position+=4
        strings.append(dictionary[position:position+size].decode('utf8'));position+=size
    assert position==len(dictionary) and len(set(strings))==count
    assert packet[:4]==b'LTV1' and packet[5:37]==hashlib.sha256(dictionary).digest()
    # LTV1: magic, one width byte, 32-byte dictionary hash, then selection count.
    width=packet[4];n=struct.unpack_from('>I',packet,37)[0]
    assert width in (7,8) and count<=2**width and len(packet)==41+(n*width+7)//8
    payload=int.from_bytes(packet[41:],'big');padding=(-n*width)%8
    assert payload&((1<<padding)-1)==0
    indices=[(payload>>(len(packet[41:])*8-width*(k+1)))&((1<<width)-1) for k in range(n)]
    assert all(i<count for i in indices)
    return ''.join(strings[i] for i in indices),strings,indices,width

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    source_manifest=json.loads((ROOT/'generated/manifest.json').read_text())
    qualified=json.loads((ROOT/'qualification/report.json').read_text())
    results=json.loads((ROOT/'search-v2/summary.json').read_text())
    assert qualified['generated_manifest_sha256']==sha((ROOT/'generated/manifest.json').read_bytes())
    assert results['qualification_sha256']==sha((ROOT/'qualification/report.json').read_bytes())
    assert results['source_manifest_sha256']==sha((ROOT/'generated/manifest.json').read_bytes())
    assert results['search_sha256']==sha((ROOT/'search.py').read_bytes())
    assert source_manifest['generator_sha256']==sha((ROOT/'generate.cjs').read_bytes())
    assert source_manifest['prior_generator_sha256']==sha((ROOT.parent/'clusters-v1/generate.cjs').read_bytes())
    sources={}
    for row in source_manifest['rows']:
        text=(ROOT/'generated'/row['file']).read_bytes();assert sha(text)==row['sha256']
        sources[(row['id'],row['variant'])]=row
    assert len(sources)==240 and qualified['passed_sources']==240
    q={(r['id'],r['variant']):r for r in qualified['rows']}
    for key,row in sources.items():
        assert q[key]['sha256']==row['sha256'] and q[key]['passed'] and not q[key]['failures']
    packet_count=0;comparison=[]
    old=json.loads((ROOT.parent/'clusters-v1/contract.json').read_text())
    old_ids={i for cluster in old['clusters'].values() for i in cluster['fit']}
    for manifest_path in sorted((ROOT/'search-v2').glob('*/manifest.json')):
        folder=manifest_path.parent;m=json.loads(manifest_path.read_text());metrics=m['metrics'];counts=[];single=0;old_counts=[];chars=0
        raw=(folder/'dictionary.ltd').read_bytes();assert sha(raw)==m['dictionary_sha256']
        for row in m['programs']:
            packet=(folder/f"{row['id']}.ltv").read_bytes();assert sha(packet)==row['packet_sha256']
            text,strings,seq,width=unpack(raw,packet)
            assert sha(text.encode())==row['source_sha256']==sources[(row['id'],metrics['arm'])]['sha256']
            assert seq==row['sequence'] and len(seq)==row['selections']
            assert len(strings)==metrics['entries'] and width==metrics['bits_per_selection']
            counts.append(len(seq));single+=sum(len(strings[i])==1 for i in seq);chars+=len(text)
            if row['id'] in old_ids:old_counts.append(len(seq))
            packet_count+=1
        assert len(counts)==80 and sum(counts)==metrics['selections'] and single==metrics['single_character_selections']
        assert len(raw)+sum(f.stat().st_size for f in folder.glob('*.ltv'))==metrics['package_bytes']
        assert metrics['whole_program_literals']==0
        comparison.append({'package':folder.name,**metrics,'single_character_source_fraction':single/chars,
                           'prior48_selections':sum(old_counts),'prior48_median':statistics.median(old_counts),'prior48_worst':max(old_counts)})
    for p in (ROOT/'qualification/observations').glob('0942-*.stdout'):
        for line in p.read_text().splitlines():
            record=json.loads(line)
            if 'result' in record:assert all(type(v) is int for v in record['result'])
    provenance=json.loads((ROOT/'additional-provenance.json').read_text())
    for row in provenance['rows']:assert sha((ROOT/'inputs'/f"{row['id']:04d}.js").read_bytes())==row['source_sha256']
    for i,row in old['selected'].items():assert sha((ROOT/'inputs'/f'{int(i):04d}.js').read_bytes())==row['sha256']
    # Native stdout/stderr bytes remain tied to the corresponding call receipt.
    for row in qualified['rows']:
        for k,call in enumerate(row['calls']):
            stem=f"{row['id']:04d}-{row['variant']}-{k*256}"
            for suffix in ['stdout','stderr']:
                assert sha((ROOT/'qualification/observations'/f'{stem}.{suffix}').read_bytes())==call[suffix+'_sha256']
    audit={'schema':'gamma.literal-scale-audit.v2','qualified_problems':80,'qualified_source_variants':240,
           'check_executions':qualified['checks_total'],'distinct_development_cases':qualified['distinct_cases'],
           'packets_independently_decoded':packet_count,'comparisons':comparison,
           'implementation_hashes':{f:sha((ROOT/f).read_bytes()) for f in ['generate.cjs','search.py','verify.py','checks.py','audit.py']},
           'scope':'Reconstruction and hash-joined execution evidence. Same source bytes reuse recorded native execution; this audit does not rerun JavaScript.'}
    a.output.write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k not in ['comparisons','implementation_hashes']}))

if __name__=='__main__':main()
