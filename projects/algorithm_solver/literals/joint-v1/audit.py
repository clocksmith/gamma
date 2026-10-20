"""Independent decoding, source-receipt joins and exact accepted-move replay."""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parent
SCALE = ROOT.parent/'scale-v2'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
spec = importlib.util.spec_from_file_location('packet_audit', SCALE/'audit.py')
packet_audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packet_audit)


def minimum_count(text, vocab):
    # Forward DP, separate from the searcher's backward trie implementation.
    by_first = defaultdict(list)
    for s in vocab:
        by_first[s[0]].append(s)
    costs = [len(text)+1]*(len(text)+1)
    costs[0] = 0
    for start, char in enumerate(text):
        for s in by_first[char]:
            if text.startswith(s, start):
                end = start+len(s)
                costs[end] = min(costs[end], costs[start]+1)
    return costs[-1]


def score(sources, vocab, width):
    chosen = {}
    for pid, variants in sources.items():
        count, _, variant = min((minimum_count(text, vocab),len(text.encode()),v) for v,text in variants.items())
        chosen[pid] = (variant,count)
    dictionary_bytes = 8+sum(4+len(s.encode()) for s in vocab)
    packets = sum(41+(count*width+7)//8 for _,count in chosen.values())
    return {'selections':sum(n for _,n in chosen.values()),'package_bytes':dictionary_bytes+packets,
            'dictionary_bytes':dictionary_bytes,'packet_bytes':packets,'entries':len(vocab)}, chosen


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    summary=json.loads((args.run/'summary.json').read_text())
    contract=json.loads((ROOT/'contract.json').read_text())
    assert sha((ROOT/'search.py').read_bytes())==summary['search_sha256']
    assert sha((ROOT/'contract.json').read_bytes())==summary['contract_sha256']
    for path,digest in contract['inputs'].items():assert sha((ROOT/path).read_bytes())==digest
    manifest=json.loads((SCALE/'generated/manifest.json').read_text())
    qualification=json.loads((SCALE/'qualification/report.json').read_text())
    q={(r['id'],r['variant']):r for r in qualification['rows']}
    sources=defaultdict(dict);metadata={}
    for r in manifest['rows']:
        if r['variant'] not in ['canonical','compact']:continue
        key=(r['id'],r['variant']);text=(SCALE/'generated'/r['file']).read_text()
        assert sha(text.encode())==r['sha256']==q[key]['sha256'] and q[key]['passed'] and not q[key]['failures']
        assert r['entry']=='solve' and r['interface']=='named-function'
        sources[r['id']][r['variant']]=text;metadata[key]=r
        for k,call in enumerate(q[key]['calls']):
            for suffix in ['stdout','stderr']:
                path=SCALE/'qualification/observations'/f"{r['id']:04d}-{r['variant']}-{k*256}.{suffix}"
                assert sha(path.read_bytes())==call[suffix+'_sha256']
    packets=0;accepted=0;comparisons=[];counts_of_moves=Counter();variants_changed=0
    for record in summary['runs']:
        folder=args.run/record['label'];mp=folder/'manifest.json';tp=args.run/(record['label']+'-trace.json')
        assert sha(mp.read_bytes())==record['manifest_sha256'] and sha(tp.read_bytes())==record['trace_sha256']
        m=json.loads(mp.read_text());trace=json.loads(tp.read_text());metrics=m['metrics'];width=metrics['bits_per_selection']
        assert metrics==record['metrics']
        raw=(folder/'dictionary.ltd').read_bytes();assert sha(raw)==m['dictionary_sha256']
        counts=[];singles=0;owners=defaultdict(set);packet_bytes=0;seen=set()
        for r in m['programs']:
            packet=(folder/f"{r['id']}.ltv").read_bytes();assert sha(packet)==r['packet_sha256']
            text,vocab,seq,w=packet_audit.unpack(raw,packet)
            key=(r['id'],r['variant']);assert key in metadata
            assert text==sources[key[0]][key[1]] and sha(text.encode())==r['source_sha256']==metadata[key]['sha256']
            assert r['source_file']=='../scale-v2/generated/'+metadata[key]['file']
            assert seq==r['sequence'] and len(seq)==r['selections'] and width==w
            assert r['selection_bits']==width*len(seq) and r['entry']=='solve' and r['interface']=='named-function'
            assert r['id'] not in seen;seen.add(r['id']);counts.append(len(seq));packet_bytes+=len(packet)
            singles+=sum(len(vocab[i])==1 for i in seq)
            for i in seq:owners[i].add(r['id'])
            packets+=1
        assert seen==set(sources)
        assert len(vocab)==metrics['entries'] and packet_bytes==metrics['packet_bytes']
        assert len(raw)==metrics['dictionary_bytes'] and len(raw)+packet_bytes==metrics['package_bytes']
        assert sum(counts)==metrics['selections'] and singles==metrics['single_character_selections']
        assert singles/sum(counts)==metrics['single_character_selection_fraction']
        assert statistics.median(counts)==metrics['median_selections'] and max(counts)==metrics['worst_selections']
        assert sorted(counts)[math.ceil(.95*len(counts))-1]==metrics['p95_selections']
        assert set(chr(i) for i in range(32,127))|{'\n'} <= set(vocab)
        assert not set(vocab)&{t for vs in sources.values() for t in vs.values()}
        exact,chosen=score(sources,vocab,width)
        for k,v in exact.items():assert metrics[k]==v
        assert {r['id']:(r['variant'],r['selections']) for r in m['programs']}==chosen
        # Replay accepted decisions from their frozen seed, without incremental caches.
        current=set(trace['initial_dictionary']);before,_=score(sources,current,width)
        assert before==trace['initial']
        for round_ in trace['rounds']:
            assert round_['before']==before
            for attempt in round_['attempts']:
                counts_of_moves[f"{len(attempt['remove'])}-remove/{len(attempt['add'])}-add"]+=1
            if round_['accepted']:
                move=round_['accepted'];current.difference_update(move['remove']);current.update(move['add'])
                measured,_=score(sources,current,width);assert measured==move['result']
                current.difference_update(round_['pruned_after_move']);accepted+=1
                variants_changed+=len(move['source_changes'])
                after,_=score(sources,current,width)
                key=['selections','package_bytes'] if record['objective']=='input' else ['package_bytes','selections']
                assert tuple(after[k] for k in key)<tuple(before[k] for k in key)
                before=after
            assert before==round_['after']
        assert current==set(vocab) and before==exact
        comparisons.append({'label':record['label'],**metrics})
    output={'schema':'gamma.literal-joint-audit.v1','host':summary['host'],'passed':True,
            'packets_independently_decoded':packets,'qualified_source_versions_checked':len(metadata),
            'accepted_moves_independently_replayed':accepted,'accepted_source_changes':variants_changed,
            'attempt_counts':dict(counts_of_moves),'total_trials':sum(counts_of_moves.values()),
            'comparisons':comparisons,'summary_sha256':sha((args.run/'summary.json').read_bytes()),
            'audit_sha256':sha(Path(__file__).read_bytes()),
            'scope':'Independent packet/source receipt joins and selected-move optimization audit. No fresh JavaScript execution or generalization test.'}
    args.output.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ['comparisons']}))


if __name__=='__main__':main()
