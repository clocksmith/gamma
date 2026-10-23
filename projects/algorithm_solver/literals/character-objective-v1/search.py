"""Exact fixed-source dictionary search for the integer objective 4*N + weight*C."""
from collections import Counter,defaultdict
import importlib.util
from itertools import combinations
from pathlib import Path
import sys
import time
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'cost-decomposition-v1'));import analyze
spec=importlib.util.spec_from_file_location('char_search_v3',LIT/'matched80-v3/run.py');v3=importlib.util.module_from_spec(spec);spec.loader.exec_module(v3)
Budget=v3.Budget;FALLBACK=set(v3.base.ALPHABET)


def trie(vocab):
    tree={}
    for i,word in enumerate(vocab):
        node=tree
        for ch in word:node=node.setdefault(ch,{})
        node[None]=i
    return tree


def encode(text,vocab,weight,tree=None):
    tree=tree if tree is not None else trie(vocab);n=len(text)
    costs=[None]*(n+1);costs[n]=(0,0,0);edges=[None]*n
    for pos in range(n-1,-1,-1):
        node=tree;end=pos
        while end<n and text[end] in node:
            node=node[text[end]];end+=1
            if None not in node or costs[end] is None:continue
            i=node[None];c=int(len(vocab[i])==1);future=costs[end]
            value=(future[0]+4+weight*c,future[1]+1,future[2]+c)
            if costs[pos] is None or (value,i)<(costs[pos],edges[pos][0]):costs[pos]=value;edges[pos]=(i,end)
    if costs[0] is None:raise ValueError('unrepresentable')
    result=[];pos=0
    while pos<n:
        i,pos=edges[pos];result.append(i)
    return result


def evaluate(texts,vocab,width,weight,parent,budget,relaxed=False):
    budget.trials+=1;vocab=v3.joint.order(vocab)
    if parent is not None:assert parent['weight']==weight
    assert len(vocab)<=2**(width+relaxed)
    tree=trie(vocab);delta=set(vocab)^set(parent['vocab']) if parent else None;parsed={}
    for pid,text in sorted(texts.items()):
        if parent is not None and not any(word in text for word in delta):parts=parent['parsed'][pid]
        else:parts=tuple(vocab[i] for i in encode(text,vocab,weight,tree))
        parsed[pid]=parts
    n=sum(len(parts) for parts in parsed.values());c=sum(len(word)==1 for parts in parsed.values() for word in parts)
    db=len(analyze.dictionary_bytes(vocab));pb=sum(41+(width*len(parts)+7)//8 for parts in parsed.values())
    return {'vocab':vocab,'parsed':parsed,'selections':n,'characters':c,'objective':4*n+weight*c,
            'package_bytes':db+pb,'dictionary_bytes':db,'packet_bytes':pb,'weight':weight}


def cost(state):return state['objective'],state['selections'],state['characters'],state['package_bytes']


def brief(state):return {k:v for k,v in state.items() if k not in ('vocab','parsed')}|{'entries':len(state['vocab'])}


def prune(texts,state,width,weight,budget):
    used={word for parts in state['parsed'].values() for word in parts}
    removed=set(state['vocab'])-used-FALLBACK
    if not removed or budget.expired():return state,[]
    result=evaluate(texts,set(state['vocab'])-removed,width,weight,state,budget)
    assert cost(result)[:3]==cost(state)[:3]
    return result,sorted(removed)


def propose(texts,state,limit,banned):
    scores=defaultdict(int);owners=defaultdict(set);present=set(state['vocab']);w=state['weight']
    for pid,parts in state['parsed'].items():
        for start in range(len(parts)):
            for length in range(2,7):
                if start+length>len(parts):break
                words=parts[start:start+length];fragment=''.join(words)
                if len(fragment)>160 or fragment in banned or fragment in present:continue
                scores[fragment]+=4*(length-1)+w*sum(len(s)==1 for s in words);owners[fragment].add(pid)
    return sorted((s for s in scores if len(owners[s])>=2),key=lambda s:(-scores[s],len(s),s))[:limit]


def best_move(sources, state, width, weight, banned, nb, budget):
    """Exact deletion harm and addition gain screen swaps and double swaps; the best exact move wins."""
    vocab = set(state['vocab'])
    learned = [s for s in state['vocab'] if s not in FALLBACK]
    found, move, tested = None, None, set()

    def consider(remove=(), add=(), relaxed=False):
        nonlocal found, move
        candidate = (vocab - set(remove)) | set(add)
        identity = (tuple(sorted(candidate)), relaxed)
        if identity in tested or budget.expired() or (not relaxed and len(candidate) > 2**width):
            return None
        tested.add(identity)
        result = evaluate(sources, candidate, width, weight, state, budget, relaxed)
        if not relaxed and cost(result) < cost(found or state):
            found, move = result, {'remove': list(remove), 'add': list(add)}
        return result

    harm = {}
    for fragment in learned:
        result = consider(remove=[fragment])
        if result:
            harm[fragment] = result['objective'] - state['objective']
    room = len(vocab) < 2**width
    gain = {}
    for fragment in propose(sources, state, nb['additions'], banned):
        result = consider(add=[fragment], relaxed=not room)
        if result:
            gain[fragment] = state['objective'] - result['objective']
    swaps = sorted(((gain[a] - harm[r], r, a) for r in harm for a in gain), key=lambda x: (-x[0], x[1], x[2]))
    for _, remove, add in swaps[:nb['swaps']]:
        consider(remove=[remove], add=[add])
    top = sorted(gain, key=lambda a: (-gain[a], a))[:nb['pair_additions']]
    low = sorted(harm, key=lambda r: (harm[r], r))[:nb['pair_removals']]
    need = max(0, len(vocab) + 2 - 2**width)
    doubles = sorted(((gain[a] + gain[b] - sum(harm[r] for r in rem), rem, (a, b))
                      for a, b in combinations(top, 2) for rem in combinations(low, need)), key=lambda x: (-x[0], x[1], x[2]))
    for _, remove, add in doubles[:nb['pairs']]:
        consider(remove=remove, add=add)
    return found, move


def local_search(sources, state, width, weight, banned, nb, budget, log):
    while not budget.expired():
        found, move = best_move(sources, state, width, weight, banned, nb, budget)
        if found is None:
            return state, budget.reason() if budget.expired() else 'local_optimum'
        state, pruned = prune(sources, found, width, weight, budget)
        log.append({'move': move, 'pruned': pruned, 'after': brief(state), 'trials': budget.trials})
    return state, budget.reason()


def refill(sources, state, width, weight, banned, nb, limit, budget):
    """Greedy exact refill after a kick: best measured addition from the shortlist until full or no gain."""
    added = []
    while len(state['vocab']) < 2**width and not budget.expired():
        best = None
        for fragment in propose(sources, state, limit, banned):
            if budget.expired():
                break
            result = evaluate(sources, set(state['vocab']) | {fragment}, width, weight, state, budget)
            if cost(result)[:3] < cost(state)[:3] and (best is None or cost(result) < cost(best[0])):
                best = (result, fragment)
        if best is None:
            break
        state, _ = prune(sources, best[0], width, weight, budget)
        added.append(best[1])
    return state, added
