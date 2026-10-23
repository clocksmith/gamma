"""Fit-only alphabet and occurrence-proposal ablations, using exact literal costs."""
import argparse
from collections import Counter, defaultdict
import concurrent.futures
import importlib.util
import json
import math
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sys.path.insert(0, str(LIT/'cost-decomposition-v1'))
import analyze


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def category(label):
    return 'syntax' if label.startswith('syntax.') else label


def mine(texts, labels, target, forbidden, per_bucket=1024):
    """Bounded all-position fit-only pool, support >=2 distinct problems.

    Four length strata avoid spending the entire pool on long frequent strings.
    Repeated occurrences are proposals only; exact DP decides every move.
    """
    scores, support = Counter(), Counter()
    buckets = [(2,4), (5,8), (9,16), (17,24)]
    for pid, text in sorted(texts.items()):
        own = set()
        for i in range(len(text)):
            for length in range(2, min(24, len(text)-i)+1):
                piece = text[i:i+length]
                if piece in forbidden or not any(category(x)==target for x in labels[str(pid)][i:i+length]):
                    continue
                scores[piece] += length-1
                own.add(piece)
        support.update(own)
    pool = []
    for lo, hi in buckets:
        eligible = [t for t in scores if lo <= len(t) <= hi and support[t] >= 2]
        pool.extend(sorted(eligible,key=lambda t:(-scores[t],len(t),t))[:per_bucket])
    occurrences = {}
    for piece in pool:
        occ = []
        for pid,text in sorted(texts.items()):
            offset = text.find(piece)
            while offset >= 0:
                occ.append((pid,offset,offset+len(piece)))
                offset = text.find(piece,offset+1)
        occurrences[piece]=occ
    return occurrences


def occurrence_proposer(occurrences, span_proposer, texts, labels, target):
    def propose(sources, state, limit, fraction):
        prefixes, tail_prefixes = {}, {}
        for pid, variant in state['chosen'].items():
            units, tail = [], []
            offset = 0
            for piece in state['parsed'][pid,variant]:
                units.extend([1/len(piece)]*len(piece))
                tail.extend([int(len(piece)==1 and category(labels[str(pid)][offset])==target)]*len(piece))
                offset += len(piece)
            p,q = [0.],[0]
            for x,y in zip(units,tail):
                p.append(p[-1]+x);q.append(q[-1]+y)
            prefixes[pid],tail_prefixes[pid]=p,q
        candidates=[]
        present=set(state['vocab'])
        for piece,occ in occurrences.items():
            if piece in present:
                continue
            score=0.
            for pid,i,j in occ:
                if tail_prefixes[pid][j]>tail_prefixes[pid][i]:
                    score += max(0.,prefixes[pid][j]-prefixes[pid][i]-1)
            if score>1e-9:
                candidates.append((-round(score,9),len(piece),piece))
        ranked=[t for _,_,t in sorted(candidates)]
        old=span_proposer(sources,state,limit, fraction)
        head=old[:limit//2]
        for piece in ranked+old[limit//2:]:
            if piece not in head:
                head.append(piece)
            if len(head)>=limit:
                break
        return head
    return propose


def source_structure(texts):
    p=subprocess.run(['node',str(HERE/'structure.cjs')],input=json.dumps(texts),text=True,capture_output=True,check=True)
    return json.loads(p.stdout)


def evaluate_output(texts,vocab,width,forbidden,labels=None):
    db=analyze.dictionary_bytes(vocab)
    rows={}
    assert len(set(vocab))==len(vocab)<=2**width
    illegal=sorted(analyze.sha(t.encode()) for t in set(vocab)&forbidden)
    for pid,text in sorted(texts.items()):
        try:
            seq=analyze.shortest_encode(text,vocab)
        except ValueError:
            rows[str(pid)]={'encodable':False,'source_sha256':analyze.sha(text.encode())}
            continue
        packet=analyze.encode(vocab,seq,width)
        assert analyze.decode(db,packet)==text
        rows[str(pid)]={'encodable':True,'source_sha256':analyze.sha(text.encode()),'selections':len(seq),
                        'actions':len(seq)+1,'single_characters':sum(len(vocab[i])==1 for i in seq),'packet_bytes':len(packet)}
        if labels is not None:
            attr=analyze.attribute(text,vocab,seq,labels[str(pid)])
            rows[str(pid)].update({k:attr[k] for k in ('fractional_selections','single_character_selections')})
    return rows,illegal


def aggregate(rows, ids, dictionary_size):
    good=[rows[str(pid)] for pid in ids if rows[str(pid)]['encodable']]
    total=sum(r['selections'] for r in good)
    fractions,single=Counter(),Counter()
    for row in good:
        fractions.update(row.get('fractional_selections',{}));single.update(row.get('single_character_selections',{}))
    return {'problems':len(ids),'covered':len(good),'failed_ids':[p for p in ids if not rows[str(p)]['encodable']],
            'selections':analyze.distribution([r['selections'] for r in good]) if good else None,
            'actions':analyze.distribution([r['actions'] for r in good]) if good else None,
            'single_character_fraction':sum(r['single_characters'] for r in good)/total if total else None,
            'package_bytes':dictionary_size+sum(r['packet_bytes'] for r in good),
            'package_scope':'encoded programs only; failed programs retained in coverage denominator',
            'fractional_selections':dict(fractions),'single_character_selections':dict(single)}


def arm(job):
    name,width,work,out=job['name'],job['width'],Path(job['work']),Path(job['output'])
    c=json.loads((HERE/'contract.json').read_text())
    for rel,digest in c['code_hashes'].items():
        assert analyze.sha((LIT/rel).read_bytes())==digest,rel
    parent=json.loads((LIT/'cost-decomposition-v1/contract.json').read_text())
    assert analyze.sha((LIT/'cost-decomposition-v1/contract.json').read_bytes())==c['parent_contract_sha256']
    assert analyze.sha(Path(c['acorn']['file']).read_bytes())==c['acorn']['sha256']
    # The optimizer receives fit sources only. Validation is loaded after final dictionary sealing.
    fit_ids=parent['partition']['dev_fit']; val_ids=parent['partition']['dev_val']
    fit_contract={**parent,'sources':[r for r in parent['sources'] if r['id'] in set(fit_ids)]}
    texts=analyze.load_sources(work,fit_contract)
    structure=source_structure(texts)
    forbidden=set(texts.values())|{s for r in structure.values() for s in r['bodies']}
    labels={pid:r['labels'] for pid,r in structure.items()}
    raw=(work/parent['dictionaries'][str(width)]['relative_path']).read_bytes()
    assert analyze.sha(raw)==parent['dictionaries'][str(width)]['sha256']
    baseline=json.loads(raw)
    m2=module('tail_style_v2',LIT/'style150-v2/measure.py')
    v3,joint=m2.v3,m2.joint
    full_alphabet=[chr(i) for i in range(32,127)]+['\n']
    observed=set(''.join(texts.values()))
    assert observed <= set(full_alphabet)
    alphabet=[ch for ch in full_alphabet if ch in observed] if name in ('alphabet','joint') else full_alphabet
    joint.base.ALPHABET=alphabet
    v3.FALLBACK=set(alphabet)
    sources={pid:{'style':t} for pid,t in texts.items()}
    starting=[t for t in baseline if len(t)>1 or t in alphabet]
    assert not set(starting)&forbidden
    budget=v3.Budget({'trials':c['search']['trials'],'seconds':c['search']['seconds']})
    started=time.monotonic()
    state=v3.evaluate(sources,starting,width,None,budget)
    starting_cost=state['selections']
    old=m2.hybrid_chosen([],sources)
    if name in ('positions','joint'):
        occurrences=mine(texts,labels,c['target'],forbidden,c['search']['per_length_bucket'])
        propose=occurrence_proposer(occurrences,old,texts,labels,c['target'])
        pool_hash=analyze.sha(json.dumps(sorted(occurrences)).encode())
    else:
        occurrences={};propose=old;pool_hash=None
    # Apply whole-body exclusion to every newly proposed string, including old span proposals.
    raw_propose=propose
    def safe(s,st,limit,fraction):
        return [p for p in raw_propose(s,st,limit,fraction) if p not in forbidden]
    nb=c['search']['neighborhood']
    state,_=v3.refill(sources,state,width,safe,nb,c['search']['refill_shortlist'],budget)
    log=[]
    state,stop=v3.local_search(sources,state,width,safe,nb,budget,log)
    assert state['selections']<=starting_cost
    vocab=state['vocab']
    folder=out/f'{name}-{2**width}';folder.mkdir()
    analyze.write(folder/'dictionary.json',vocab)
    analyze.write(folder/'trace.json',{'rounds':log,'stop':stop})
    dictionary_hash=analyze.sha((folder/'dictionary.json').read_bytes())
    analyze.write(folder/'fit-seal.json',{'dictionary_sha256':dictionary_hash,'fit_ids':fit_ids,
                  'fit_selections':state['selections'],'validation_loaded':False})
    # Once sealed, parse the 100 validation sources without feeding them to search.
    val_contract={**parent,'sources':[r for r in parent['sources'] if r['id'] in set(val_ids)]}
    validation=analyze.load_sources(work,val_contract)
    val_structure=source_structure(validation)
    all_forbidden=forbidden|set(validation.values())|{s for r in val_structure.values() for s in r['bodies']}
    all_labels={**labels,**{pid:r['labels'] for pid,r in val_structure.items()}}
    rows,illegal=evaluate_output({**texts,**validation},vocab,width,all_forbidden,all_labels)
    db=len(analyze.dictionary_bytes(vocab))
    result={'arm':name,'width':width,'entries':len(vocab),'dictionary_bytes':db,
            'dictionary_sha256':dictionary_hash,'per_problem':rows,'illegal_entry_sha256':illegal,
            'fit':aggregate(rows,fit_ids,db),'validation':aggregate(rows,val_ids,db),
            'alphabet_entries':len(alphabet),'start_fit_selections':starting_cost,'trials':budget.trials,
            'stop':stop,'seconds':time.monotonic()-started,'candidate_pool_count':len(occurrences),'candidate_pool_sha256':pool_hash}
    analyze.write(folder/'results.json',result)
    print(json.dumps({k:result[k] for k in ('arm','width','trials','stop','seconds','fit','validation')}),flush=True)
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--parallel',type=int,default=4);a=ap.parse_args()
    assert 1<=a.parallel<=12
    a.output.mkdir(parents=True,exist_ok=False)
    jobs=[{'name':n,'width':w,'work':str(a.work.resolve()),'output':str(a.output.resolve())}
          for w in (7,8) for n in ('control','alphabet','positions','joint')]
    started=time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.parallel,mp_context=multiprocessing.get_context('spawn')) as pool:
        results=list(pool.map(arm,jobs))
    analyze.write(a.output/'results.json',{'schema':'gamma.tail-search.v1','contract_sha256':analyze.sha((HERE/'contract.json').read_bytes()),
                  'arms':results,'seconds':time.monotonic()-started})


if __name__=='__main__':
    main()
