"""Independent exact packet, binding-source and native-receipt audit."""
import argparse
from collections import Counter,defaultdict
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
spec=importlib.util.spec_from_file_location('joint_audit',ROOT.parent/'joint-v1/audit.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    contract=json.loads((ROOT/'contract.json').read_text());search_contract=json.loads((ROOT/'search-contract.json').read_text())
    for c in [contract,search_contract]:
        for path,digest in c['inputs'].items():assert sha((ROOT/path).read_bytes())==digest,path
    generated=json.loads((ROOT/'generated/manifest.json').read_text());qualification=json.loads((ROOT/'qualification/report.json').read_text())
    assert generated['generator_sha256']==sha((ROOT/'generate.cjs').read_bytes())
    assert generated['contract_sha256']==sha((ROOT/'contract.json').read_bytes())
    assert qualification['generated_manifest_sha256']==sha((ROOT/'generated/manifest.json').read_bytes())
    assert qualification['passed_sources']==qualification['source_count']==460
    qnew={(r['id'],r['variant']):r for r in qualification['rows']}
    for r in generated['rows']:
        assert sha((ROOT/'generated'/r['file']).read_bytes())==r['sha256']==qnew[(r['id'],r['variant'])]['sha256']
        if 'parent' in r:assert sha((ROOT/r['parent']['file']).read_bytes())==r['parent']['sha256']
    pool=json.loads((ROOT/'proposals.json').read_text());assert pool['generator_sha256']==sha((ROOT/'fragment-proposals.cjs').read_bytes())
    sources=defaultdict(dict);metadata={};banned=set();owners=defaultdict(set)
    qold={(r['id'],'old-'+r['variant']):r for r in json.loads((ROOT.parent/'scale-v2/qualification/report.json').read_text())['rows']}
    for r in pool['rows']:
        text=(ROOT/r['file']).read_text();assert sha(text.encode())==r['sha256']
        key=(r['id'],r['variant']);q=(qold if r['variant'].startswith('old-') else qnew)[key]
        assert q['passed'] and not q['failures'] and q['sha256']==r['sha256']
        metadata[key]=r;sources[r['id']][r['variant']]=text;banned.update(r['excluded'])
        for s in r['fragments']:owners[s].add(r['id'])
    assert len(metadata)==540 and set(sources)==set(contract['prior_ids']+contract['additional_ids'])
    for basedir,report in [(ROOT,qualification),(ROOT.parent/'scale-v2',json.loads((ROOT.parent/'scale-v2/qualification/report.json').read_text()))]:
        for row in report['rows']:
            for k,call in enumerate(row['calls']):
                for suffix in ['stdout','stderr']:
                    assert sha((basedir/'qualification/observations'/f"{row['id']:04d}-{row['variant']}-{k*256}.{suffix}").read_bytes())==call[suffix+'_sha256']
    summary=json.loads((ROOT/'search-v1/summary.json').read_text())
    assert summary['search_sha256']==sha((ROOT/'search.py').read_bytes()) and summary['contract_sha256']==sha((ROOT/'search-contract.json').read_bytes())
    packets=0;comparisons=[];accepted=0;source_switches=0
    for mp in sorted((ROOT/'search-v1').glob('*/manifest.json')):
        m=json.loads(mp.read_text());metrics=m['metrics'];folder=mp.parent;raw=(folder/'dictionary.ltd').read_bytes()
        assert sha(raw)==m['dictionary_sha256'];counts=[];single=0;size=0;seen=set()
        for r in m['programs']:
            packet=(folder/f"{r['id']}.ltv").read_bytes();assert sha(packet)==r['packet_sha256']
            text,vocab,seq,width=prior.packet_audit.unpack(raw,packet);key=(r['id'],r['variant'])
            assert text==sources[key[0]][key[1]] and sha(text.encode())==r['source_sha256']==metadata[key]['sha256']
            assert r['source_file']==metadata[key]['file'] and r['entry']=='solve' and r['interface']=='named-function'
            assert seq==r['sequence'] and len(seq)==r['selections'] and len(seq)*width==r['selection_bits']
            assert width==metrics['bits_per_selection'];counts.append(len(seq));single+=sum(len(vocab[i])==1 for i in seq);size+=len(packet);packets+=1
            assert r['id'] not in seen;seen.add(r['id'])
        assert seen==set(sources) and len(vocab)==metrics['entries'] and not set(vocab)&banned
        assert all(len(s.encode())<=512 for s in vocab)
        assert set(chr(i) for i in range(32,127))|{'\n'} <= set(vocab)
        for s in vocab:
            if len(s)>1:assert sum(any(s in t for t in vs.values()) for vs in sources.values())>=2
        assert sum(counts)==metrics['selections'] and single==metrics['single_character_selections']
        assert single/sum(counts)==metrics['single_character_selection_fraction']
        assert statistics.median(counts)==metrics['median_selections'] and max(counts)==metrics['worst_selections']
        assert sorted(counts)[math.ceil(.95*len(counts))-1]==metrics['p95_selections']
        assert len(raw)==metrics['dictionary_bytes'] and size==metrics['packet_bytes'] and len(raw)+size==metrics['package_bytes']
        if folder.name.startswith('joint-'):
            exact,chosen=prior.score(sources,vocab,width)
            for k,v in exact.items():assert metrics[k]==v
            assert {r['id']:(r['variant'],r['selections']) for r in m['programs']}==chosen
            trace=json.loads((ROOT/'search-v1'/(folder.name+'-trace.json')).read_text())
            current=set(trace['initial_dictionary']);before,_=prior.score(sources,current,width);assert before==trace['initial']
            for step in trace['rounds']:
                assert step['before']==before
                if step['accepted']:
                    move=step['accepted'];current.difference_update(move['remove']);current.update(move['add']);actual,_=prior.score(sources,current,width);assert actual==move['result']
                    current.difference_update(step['pruned_after_move']);after,_=prior.score(sources,current,width)
                    assert (after['selections'],after['package_bytes'])<(before['selections'],before['package_bytes'])
                    accepted+=1;source_switches+=len(move['source_changes']);before=after
                assert before==step['after']
            assert current==set(vocab)
        comparisons.append({'label':folder.name,**metrics})
    best=min((r for r in comparisons if r['label'].startswith('joint-256')),key=lambda r:(r['selections'],r['package_bytes']))
    newv=json.loads((ROOT/'search-v1'/best['label']/'dictionary.json').read_text());oldv=json.loads((ROOT.parent/'scale-v2/search-v2/compact-marginal-256/dictionary.json').read_text())
    olds={i:{v:t for v,t in vs.items() if v in ['old-canonical','old-compact']} for i,vs in sources.items()}
    ablations={}
    for label,ss,vocab in [('old-sources-old-dictionary',olds,oldv),('new-source-pool-old-dictionary',sources,oldv),('old-sources-new-dictionary',olds,newv),('new-source-pool-new-dictionary',sources,newv),('unreoptimized-160-byte-cap-deletion',sources,[s for s in newv if len(s.encode())<=160])]:
        score,choice=prior.score(ss,vocab,8);ablations[label]=score|{'new_source_choices':sum(not v.startswith('old-') for v,n in choice.values())}
    output={'schema':'gamma.literal-rewrite-audit.v1','host':'128','passed':True,'distinct_problems':80,'qualified_source_choices':len(metadata),
            'new_native_source_versions':460,'new_check_executions':qualification['checks_total'],'distinct_development_cases':qualification['distinct_cases'],
            'packets_independently_decoded':packets,'accepted_joint_moves_replayed':accepted,'source_switches_during_accepted_moves':source_switches,
            'comparisons':comparisons,'ablations':ablations,'summary_sha256':sha((ROOT/'search-v1/summary.json').read_bytes()),
            'audit_sha256':sha(Path(__file__).read_bytes()),'scope':'Same80 exposed development problems. Fresh native qualification of new source bytes; packet audit reuses those execution receipts. No protected or autonomous result.'}
    a.output.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ['comparisons']}))


if __name__=='__main__':main()
