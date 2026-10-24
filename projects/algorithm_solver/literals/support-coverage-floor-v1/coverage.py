"""Supplied-input shared-only coverage floor; no private loader or q."""
import hashlib
import importlib.util
import json
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def validate(texts,pool,banned):
    if not __debug__:
        raise RuntimeError('normal assertions required')
    assert texts and all(type(p) is str and type(t) is str and t for p,t in texts.items())
    assert pool==sorted(set(pool)) and all(type(w) is str and w for w in pool)
    assert not set(pool)&set(banned)


def production(texts,pool,banned):
    validate(texts,pool,banned);trie={}
    for eid,word in enumerate(pool):
        node=trie
        for char in word:node=node.setdefault(char,{})
        node[None]=eid
    first=[None]*len(pool);shared=[False]*len(pool);occurrences={};order=hashlib.sha256();total=0
    for pid,text in sorted(texts.items()):
        edges=[[] for _ in text]
        for start in range(len(text)):
            node=trie
            for end in range(start+1,len(text)+1):
                node=node.get(text[end-1])
                if node is None:break
                if None not in node:continue
                eid=node[None];edges[start].append((end,eid));total+=1
                order.update((json.dumps([pid,start,end,eid],separators=(',',':'))+'\n').encode())
                if first[eid] is None:first[eid]=pid
                elif first[eid]!=pid:shared[eid]=True
        occurrences[pid]=edges
    success={};vectors={}
    for pid,text in sorted(texts.items()):
        reachable=[False]*(len(text)+1);reachable[0]=True
        for start,edges in enumerate(occurrences[pid]):
            if reachable[start]:
                for end,eid in edges:
                    if shared[eid]:reachable[end]=True
        success[pid]=reachable[-1];vectors[pid]=reachable
    chars={}
    for pid,text in texts.items():
        for ch in set(text):chars.setdefault(ch,set()).add(pid)
    forced_chars=sorted(set().union(*(owners for owners in chars.values() if len(owners)==1)))
    forced=sorted(pid for pid,ok in success.items() if not ok)
    assert set(forced_chars)<=set(forced)
    return {'shared_entry_ids':[i for i,yes in enumerate(shared) if yes],
            'owner_classes':[2 if shared[i] else int(first[i] is not None) for i in range(len(pool))],
            'source_success':success,'forced_source_ids':forced,'private_character_source_ids':forced_chars,
            'private_character_entries':sum(len(owners)==1 for owners in chars.values()),
            'occurrences':total,'occurrence_sha256':order.hexdigest(),'prefix_reachable':vectors}


def replay(texts,pool,banned):
    validate(texts,pool,banned)
    path=Path(__file__).resolve().parents[1]/'potential-lift-certificate-v1/independent.py'
    spec=importlib.util.spec_from_file_location('support56_matcher50',path)
    matcher_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(matcher_module)
    matcher=matcher_module.Matcher(pool);owners=[set() for _ in pool];edges={};order=hashlib.sha256();total=0
    for pid in sorted(texts):
        rows=list(matcher.occurrences(texts[pid]));edges[pid]=rows
        for start,end,eid in sorted(rows):
            owners[eid].add(pid);total+=1
            order.update((json.dumps([pid,start,end,eid],separators=(',',':'))+'\n').encode())
    shared={i for i,ids in enumerate(owners) if len(ids)>=2}
    success={};vectors={}
    for pid,text in texts.items():
        incoming=[[] for _ in range(len(text)+1)]
        for start,end,eid in edges[pid]:
            if eid in shared:incoming[end].append(start)
        reaches=[False]*(len(text)+1);reaches[-1]=True
        for end in range(len(text),0,-1):
            if reaches[end]:
                for start in incoming[end]:reaches[start]=True
        success[pid]=reaches[0];vectors[pid]=reaches
    allchars=set(''.join(texts.values()))
    privatechars={ch for ch in allchars if sum(ch in text for text in texts.values())==1}
    forced_chars=sorted(pid for pid,text in texts.items() if any(ch in text for ch in privatechars))
    forced=sorted(pid for pid,ok in success.items() if not ok);assert set(forced_chars)<=set(forced)
    return {'shared_entry_ids':sorted(shared),'owner_classes':[min(2,len(ids)) for ids in owners],
            'source_success':success,'forced_source_ids':forced,'private_character_source_ids':forced_chars,
            'private_character_entries':len(privatechars),'occurrences':total,
            'occurrence_sha256':order.hexdigest(),'suffix_reachable':vectors}
