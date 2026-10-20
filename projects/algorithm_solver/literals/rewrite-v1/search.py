"""Train dictionaries on coherent rewritten styles, then jointly select sources."""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
spec=importlib.util.spec_from_file_location('rewrite_joint',ROOT.parent/'joint-v1/search.py')
joint=importlib.util.module_from_spec(spec);spec.loader.exec_module(joint)
base=joint.base
old_proposals=joint.proposals
old_seed_proposals=base.proposals


def load():
    pool=json.loads((ROOT/'proposals.json').read_text());sources=defaultdict(dict);metadata={};owners=defaultdict(set);banned=set()
    for r in pool['rows']:
        text=(ROOT/r['file']).read_text();assert sha(text.encode())==r['sha256']
        sources[r['id']][r['variant']]=text;metadata[(r['id'],r['variant'])]=r;banned.update(r['excluded'])
        for s in r['fragments']:owners[s].add(r['id'])
    admitted={s for s,ids in owners.items() if len(ids)>=2 and s not in banned}
    return dict(sources),metadata,admitted,banned


def ast_rank(texts,vocab,admitted,limit):
    tree=base.trie(vocab);ranked=[]
    for s in admitted-set(vocab):
        occurrences=sum(max(t.count(s) for t in variants.values()) for variants in texts.values())
        if not occurrences:continue
        saving=len(base.segment(s,tree))-1
        if saving>0:ranked.append((-saving*occurrences,len(s.encode()),s))
    return [s for _,_,s in sorted(ranked)[:limit]]


def styles(sources):
    attempts=json.loads((ROOT/'generated/manifest.json').read_text())['attempts'];output={}
    for mode in ['scope','role','scope-arrow']:
        desired={a['parent']['id']:a['sha256'] for a in attempts if a['parent']['origin']=='scale' and a['mode']==mode and a['status']!='rejected'}
        choice={}
        for pid,variants in sources.items():
            matches=[v for v,t in variants.items() if sha(t.encode())==desired.get(pid)]
            choice[pid]=min(matches) if matches else 'old-compact'
        output[mode]=choice
    return output


def save(folder,sources,metadata,state,width,method):
    texts={str(pid):sources[pid][v] for pid,v in state['chosen'].items()};indices={s:i for i,s in enumerate(state['vocab'])}
    seqs={str(pid):[indices[s] for s in state['parsed'][(pid,v)]] for pid,v in state['chosen'].items()}
    metrics=base.save(folder,texts,state['vocab'],seqs,width,'qualified-rewrites',method)
    m=json.loads((folder/'manifest.json').read_text())
    for r in m['programs']:
        v=state['chosen'][r['id']];meta=metadata[(r['id'],v)]
        r.update(variant=v,source_file=meta['file'],entry='solve',interface='named-function')
    import math,statistics
    metrics['p95_selections']=sorted(r['selections'] for r in m['programs'])[math.ceil(.95*len(texts))-1]
    metrics['source_variants']=dict(Counter(state['chosen'].values()))
    metrics['new_source_problems']=sum(not v.startswith('old-') for v in state['chosen'].values())
    assert metrics['selections']==state['selections'] and metrics['package_bytes']==state['package_bytes']
    m['metrics']=metrics;joint.write(folder/'manifest.json',m)
    return metrics


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    contract=json.loads((ROOT/'search-contract.json').read_text())
    for rel,h in contract['inputs'].items():assert sha((ROOT/rel).read_bytes())==h,rel
    sources,metadata,admitted,banned=load();a.output.mkdir(exist_ok=False)
    seeds=[];seed_records=[];began=time.monotonic()
    for path in sorted((ROOT.parent/'scale-v2/search-v2').glob('*/dictionary.json')):
        vocab=json.loads(path.read_text());assert not set(vocab)&banned
        seeds.append((path.parent.name,vocab))
    # Learn separately on consistent source styles so the old dictionary does
    # not suppress mutually dependent source/literal improvements at the start.
    for style,chosen in styles(sources).items():
        texts={str(pid):sources[pid][v] for pid,v in chosen.items()}
        fixed={int(pid):{'style':text} for pid,text in texts.items()}
        def seed_proposals(ts,vocab,current):
            ast=ast_rank(fixed,vocab,admitted,8)
            spans=[s for s in old_seed_proposals(ts,vocab,current) if s not in banned][:8]
            return list(dict.fromkeys(ast+spans))
        base.proposals=seed_proposals
        snapshots,trace=base.learn(texts,contract['seed_bounds'])
        joint.write(a.output/(style+'-seed-trace.json'),trace)
        for budget,(vocab,seqs) in snapshots.items():
            assert not set(vocab)&banned
            name=f'{style}-learned-{budget}';seeds.append((name,vocab))
            state=joint.evaluate({pid:{chosen[pid]:sources[pid][chosen[pid]]} for pid in sources},vocab,budget.bit_length()-1)
            metrics=save(a.output/name,sources,metadata,state,budget.bit_length()-1,'coherent-style-ast-admission')
            seed_records.append({'label':name,'metrics':metrics})
        print(json.dumps({'style_complete':style,'trials':trace['exact_candidate_trials'],'seconds':trace['elapsed_seconds']}),flush=True)
    base.proposals=old_seed_proposals
    def joint_proposals(ss,state,limit):
        ast=ast_rank(ss,state['vocab'],admitted,limit//2)
        spans=[s for s in old_proposals(ss,state,limit) if s not in banned][:limit//2]
        return list(dict.fromkeys(ast+spans))
    joint.proposals=joint_proposals
    records=[];screen=[]
    for width in [7,8]:
        states=[]
        for name,vocab in seeds:
            if len(vocab)>2**width:continue
            state=joint.evaluate(sources,vocab,width);state,removed=joint.prune(sources,state,width)
            states.append((name,state));screen.append({'width':width,'name':name,'score':joint.brief(state),'removed':removed,'new_sources':sum(not v.startswith('old-') for v in state['chosen'].values())})
        seen=set();selected=[]
        for name,state in sorted(states,key=lambda pair:(joint.cost(pair[1],'input'),pair[0])):
            identity=tuple(state['vocab'])
            if identity in seen:continue
            seen.add(identity);selected.append((name,state))
            if len(selected)==contract['joint_bounds']['starts_per_arm']:break
        for index,(name,initial) in enumerate(selected):
            final,trace=joint.improve(sources,initial,width,'input',contract['joint_bounds'])
            label=f'joint-{2**width}-start{index}';metrics=save(a.output/label,sources,metadata,final,width,'ast-proposals-joint-qualified-rewrites')
            joint.write(a.output/(label+'-trace.json'),{'seed':name,'initial_dictionary':initial['vocab'],'initial_sources':initial['chosen'],'initial':joint.brief(initial),**trace})
            records.append({'label':label,'seed':name,'metrics':metrics,'trials':trace['trials'],'stop':trace['stop'],
                            'manifest_sha256':sha((a.output/label/'manifest.json').read_bytes()),'trace_sha256':sha((a.output/(label+'-trace.json')).read_bytes())})
    joint.write(a.output/'summary.json',{'schema':'gamma.literal-rewrite-search.v1','host':'128','scope':contract['scope'],
        'seed_records':seed_records,'seed_screen':screen,'runs':records,'qualified_source_choices':len(metadata),'admitted_ast_fragments':len(admitted),
        'elapsed_seconds':time.monotonic()-began,'contract_sha256':sha((ROOT/'search-contract.json').read_bytes()),'search_sha256':sha(Path(__file__).read_bytes())})


if __name__=='__main__':main()
