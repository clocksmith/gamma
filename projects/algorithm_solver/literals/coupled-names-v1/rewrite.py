"""Exact literal-cost coordinate descent over safe lexical name assignments."""
import importlib.util
import json
from pathlib import Path
import string
import subprocess
import sys

HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'cost-decomposition-v1'));import analyze
_spec=importlib.util.spec_from_file_location('binding_descent_codec',LIT/'clusters-v1/search.py')
codec=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(codec)


def records(texts):
    got=subprocess.run(['node',str(HERE/'structure.cjs')],input=json.dumps(texts),text=True,capture_output=True,check=True)
    return json.loads(got.stdout)


def legal(record,colors):
    return all((v['eligible'] or colors[v['id']]==v['name']) and (not v['eligible'] or colors[v['id']] not in v['forbidden']) and
        all(colors[v['id']]!=colors[j] or not (v['eligible'] or record['variables'][j]['eligible']) for j in v['neighbors']) for v in record['variables'])


def render(text,record,colors):
    assert legal(record,colors)
    edits=sorted((a,b,colors[v['id']]) for v in record['variables'] if colors[v['id']]!=v['name'] for a,b in v['spans'])
    output=[];offset=0
    for a,b,name in edits:
        assert a>=offset;output.extend([text[offset:a],name]);offset=b
    output.append(text[offset:]);return ''.join(output)


def ordinary(text,record,vocab,mode='scope',sweeps=2,max_trials=6000):
    if not text.isascii() or record['unsafe']:
        return text,{'trials':0,'moves':0,'stop':'unsupported','reason':record['reason'] or 'non_ascii','_trace':[]}
    variables=record['variables'];colors=[v['name'] for v in variables]
    assert legal(record,colors)
    if mode=='global':
        groups={}
        for v in variables:groups.setdefault(v['name'],[]).append(v['id'])
        units=[ids for ids in groups.values() if all(variables[i]['eligible'] for i in ids)]
        reserved={v['name'] for v in variables if not v['eligible']}|{name for v in variables for name in v['forbidden']}
    else:
        units=[[v['id']] for v in variables if v['eligible']];reserved=set()
    units.sort(key=lambda ids:(-sum(len(variables[i]['spans']) for i in ids),min(ids)))
    tree=codec.trie(vocab);score=lambda t:len(codec.encode_text(t,tree))
    current=text;cost=score(text);trials=moves=0;trace=[];stop='sweep_limit'
    for sweep in range(sweeps):
        changed=False
        for ui,unit in enumerate(units):
            best=None;seen=set()
            def trial(proposal):
                nonlocal trials,best
                key=tuple(proposal)
                if trials>=max_trials or key in seen or key==tuple(colors):return
                seen.add(key)
                if not legal(record,proposal):return
                if mode=='global':
                    mapped=[proposal[u[0]] for u in units]
                    if len(mapped)!=len(set(mapped)) or set(mapped)&reserved:return
                if not source_legal(text,record,proposal,vocab):return
                candidate=render(text,record,proposal);value=score(candidate);trials+=1
                trace.append({'sweep':sweep,'unit':ui,'selections':value,'sha256':analyze.sha(candidate.encode())})
                order=(value,len(candidate.encode()),candidate)
                if value<cost and (best is None or order<best[0]):best=(order,proposal,candidate)
            for letter in string.ascii_lowercase:
                if letter in reserved:continue
                proposal=list(colors)
                for i in unit:proposal[i]=letter
                trial(proposal)
            # A pair swap can cross a collision barrier, but all graph constraints still apply.
            for other in units:
                if other is unit or colors[other[0]]==colors[unit[0]]:continue
                proposal=list(colors)
                for i in unit:proposal[i]=colors[other[0]]
                for i in other:proposal[i]=colors[unit[0]]
                trial(proposal)
            if best is not None:
                order,colors,current=best;cost=order[0];moves+=1;changed=True
                trace.append({'accepted_colors':list(colors),'selections':cost,'sha256':analyze.sha(current.encode())})
            if trials>=max_trials:stop='trial_limit';break
        if trials>=max_trials:break
        if not changed:stop='local_coordinate_stop';break
    return current,{'trials':trials,'moves':moves,'stop':stop,'reason':None,'eligible_bindings':sum(v['eligible'] for v in variables),
        'units':len(units),'initial_distinct_spellings':len(set(v['name'] for v in variables)),
        'final_distinct_spellings':len(set(colors)),'_trace':trace}


def source_legal(text,record,colors,vocab):
    """Check complete source and the same solve ranges as tail-search, before scoring."""
    if render(text,record,colors) in vocab:return False
    edits=sorted((a,b,colors[v['id']]) for v in record['variables'] if colors[v['id']]!=v['name'] for a,b in v['spans'])
    for start,end in record['body_ranges']:
        parts=[];offset=start
        for a,b,name in edits:
            if a>=start and b<=end:parts.extend([text[offset:a],name]);offset=b
        parts.append(text[offset:end])
        if ''.join(parts).strip() in vocab:return False
    return True


def proposals(text,record,vocab,state_limit=100000,max_changed=3):
    """Trie alignments skip only complete eligible binding spans; no partial identifiers."""
    tree={};ends={}
    for index,word in enumerate(vocab):
        if len(word)<2:continue
        node=tree
        for ch in word:node=node.setdefault(ch,{})
        node[None]=index
    starts={a:(b,v['id']) for v in record['variables'] if v['eligible'] for a,b in v['spans']}
    interiors={i for a,(b,_) in starts.items() for i in range(a+1,b)}
    original=[v['name'] for v in record['variables']];found={};states=0;stop='exhausted'
    for start in range(len(text)):
        if start in interiors:continue
        stack=[(start,tree,{})]
        while stack:
            if states>=state_limit:stop='state_limit';return found,states,stop
            pos,node,assigned=stack.pop();states+=1
            if None in node:
                changes=tuple(sorted((i,n) for i,n in assigned.items() if n!=original[i]))
                if 2<=len(changes)<=max_changed:
                    colors=list(original)
                    for i,n in changes:colors[i]=n
                    if legal(record,colors):
                        # Rank by longest matched entry, then earliest occurrence/entry ID.
                        rank=(-len(vocab[node[None]]),start,node[None])
                        if changes not in found or rank<found[changes]:found[changes]=rank
            if pos>=len(text):continue
            if pos in starts:
                end,vid=starts[pos]
                targets=[assigned[vid]] if vid in assigned else sorted(set([original[vid]]+list(string.ascii_lowercase)))
                for name in reversed(targets):
                    cursor=node
                    for ch in name:
                        if ch not in cursor:cursor=None;break
                        cursor=cursor[ch]
                    if cursor is None:continue
                    updated={**assigned,vid:name}
                    if sum(n!=original[i] for i,n in updated.items())<=max_changed:stack.append((end,cursor,updated))
            elif text[pos] in node:stack.append((pos+1,node[text[pos]],assigned))
    return found,states,stop


def coupled(text,record,vocab,rounds=3,proposal_limit=512,state_limit=100000):
    current=text;trace=[];stats={'trials':0,'moves':0,'states':0,'proposals':0,'caps':0,'_trace':trace}
    if record['unsafe'] or not text.isascii():return current,stats
    tree=codec.trie(vocab);score=lambda s:len(codec.encode_text(s,tree))
    for round_no in range(rounds):
        rec=record if round_no==0 else records({'x':current})['x']
        found,states,stop=proposals(current,rec,vocab,state_limit)
        stats['states']+=states;stats['proposals']+=len(found)
        stats['caps']+=int(stop=='state_limit')+int(len(found)>proposal_limit)
        best=None;cost=score(current)
        for changes,rank in sorted(found.items(),key=lambda x:(x[1],x[0]))[:proposal_limit]:
            colors=[v['name'] for v in rec['variables']]
            for i,n in changes:colors[i]=n
            if not source_legal(current,rec,colors,vocab):continue
            candidate=render(current,rec,colors);value=score(candidate);stats['trials']+=1
            trace.append({'round':round_no,'changes':changes,'selections':value,'sha256':analyze.sha(candidate.encode())})
            order=(value,len(candidate.encode()),candidate)
            if value<cost and (best is None or order<best[0]):best=(order,candidate)
        if best is None:break
        current=best[1];stats['moves']+=1
    return current,stats


def optimize(text,record,vocab,mode='ordinary',sweeps=2,max_trials=6000,**limits):
    current,stats=ordinary(text,record,vocab,sweeps=sweeps,max_trials=max_trials)
    stats['coupled']={'trials':0,'moves':0,'states':0,'proposals':0,'caps':0}
    if mode=='coupled':
        rec=records({'x':current})['x'] if current!=text else record
        current,extra=coupled(current,rec,vocab,**limits)
        stats['_trace']+=extra.pop('_trace');stats['coupled']=extra
    return current,stats
