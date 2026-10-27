"""Queue 07 subset 03 source-blind bounded references; no qualification.

All statement domains remain full, including tree and transport maxima that the
frozen finite packet set explicitly omits. Native interfaces remain unknown.
"""
from itertools import product
import ast
import json
import random
import re
from . import imported_qualification as q
from .imported_clean_domains import graph, integer, ints

IDS=(2920,2925,2967,2972)
PARAMETERS={2920:('edges','coins','k'),2925:('edges','values'),2967:('nums',),2972:('nums',)}
TITLES={2920:'Maximum Points After Collecting Coins From All Nodes',2925:'Maximum Score After Applying Operations on a Tree',2967:'Minimum Cost to Make Array Equalindromic',2972:'Count the Number of Incremovable Subarrays II'}
STATEMENT_SHA256={2920:'b80d813cb6855b94957802df0da5165bc517b030595f94074c603b5bb6b1d5bf',2925:'73100faac44b17bcef4429ee4db64c42ee3e479a8b45f85803807547d7fa28a4',2967:'cc8eeb604af10070003bf78d08296e7095ce75382764c14227c58553822dfeb8',2972:'25e5872d49dc741d6266df9b6e88af1f0eed2b649604bb110cbe3aa51902e6d9'}
EXAMPLE_COUNT={2920:2,2925:2,2967:3,2972:3}
CASE_COUNT = {2920: 605, 2925: 239, 2967: 3972, 2972: 3348}
CASES_SHA256 = {2920: 'f23e4999633719d97186db37a505dedff8a15e8e77b4df6a4d98547b55cb8262', 2925: 'bec75c7d45e745407f8027adc6c57d9b61c1bfbfd9798e759375baa16499bb6d', 2967: '95bc8bd6f400c03c3de865ff10c7d55fe10e9376b45d09ade68e9c87281064a4', 2972: 'e9afdf90f7e8e030346af8351f36f1da08eed9966144df1c9cb272b344743f3f'}
SEED=202610272103


def validate(pid,args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args)!=len(PARAMETERS[pid]):raise ValueError('unsupported exact identity or ordered argument shape')
    if pid==2920:
        edges,coins,k=args;valid=ints(coins,0,10000,2,100000) and integer(k,0,10000) and graph(len(coins),edges,tree=True)
    elif pid==2925:
        edges,values=args;valid=ints(values,1,10**9,2,20000) and graph(len(values),edges,tree=True)
    else:valid=ints(args[0],1,10**9,1,100000)
    if not valid:raise ValueError('outside full pinned statement domain')


def _paths(edges,n):
    adj=[[] for _ in range(n)]
    for a,b in edges:adj[a].append(b);adj[b].append(a)
    parent=[-1]*n;order=[0];masks=[0]*n;masks[0]=1
    for node in order:
        for child in adj[node]:
            if child!=parent[node]:parent[child]=node;masks[child]=masks[node]|(1<<child);order.append(child)
    leaves=[node for node in order if node!=0 and len(adj[node])==1]
    return masks,leaves


def expected(pid,args):
    validate(pid,args)
    if pid==2920 and len(args[1])<=10:
        edges,coins,k=args;paths,_=_paths(edges,len(coins));best=0
        for choices in range(1<<len(coins)):
            total=0
            for i,value in enumerate(coins):
                inherited=(choices & (paths[i] ^ (1<<i))).bit_count();current=value//(1<<inherited)
                total+=current//2 if choices>>i&1 else current-k
            best=max(best,total)
        return best
    if pid==2925 and len(args[1])<=12:
        edges,values=args;paths,leaves=_paths(edges,len(values));best=0
        for retained in range(1<<len(values)):
            if all(retained & paths[leaf] for leaf in leaves):best=max(best,sum(v for i,v in enumerate(values) if not(retained>>i&1)))
        return best
    if pid==2967 and len(args[0])<=8 and max(args[0])<=1000:
        a=args[0]
        return min(sum(abs(x-y) for x in a) for y in range(1,2*max(a)+1) if str(y)==str(y)[::-1])
    if pid==2972 and len(args[0])<=60:
        a=args[0];answer=0
        for i in range(len(a)):
            for j in range(i+1,len(a)+1):
                remaining=a[:i]+a[j:];answer+=all(x<y for x,y in zip(remaining,remaining[1:]))
        return answer
    raise ValueError('bounded independent reference budget exceeded')


def public_examples(pid,raw):
    if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw)!=STATEMENT_SHA256[pid]:raise ValueError('exact pinned statement bytes required')
    body=re.sub(r'^L\d+: ?','',raw.decode(),flags=re.M)
    if f'{pid}. {TITLES[pid]}' not in body:raise ValueError('numeric identity/title mismatch')
    examples=[]
    for match in re.finditer(r'Input:\s*(.*?)\n\s*Output:\s*([^\n]+)',body,re.S):
        call=ast.parse('f('+match[1].strip()+')',mode='eval').body
        if not isinstance(call,ast.Call) or call.args or tuple(x.arg for x in call.keywords)!=PARAMETERS[pid]:raise ValueError('ordered example parameters mismatch')
        args=[ast.literal_eval(x.value) for x in call.keywords];answer=json.loads(match[2])
        if not q.exact(expected(pid,args),answer):raise ValueError('reference disagrees with public example')
        examples.append({'args':args,'expected':answer,'compare':'return'})
    if len(examples)!=EXAMPLE_COUNT[pid]:raise ValueError('complete pinned public examples required')
    return examples


def _generate_cases(pid,raw):
    cases=[];categories=[];seen={};rng=random.Random(SEED+pid);absent=object()
    def add(args,category,answer=absent):
        validate(pid,args);result=expected(pid,args) if answer is absent else answer;key=q.encoded(args)
        if key in seen:
            i=seen[key]
            if not q.exact(cases[i]['expected'],result):raise ValueError('conflicting duplicate expectation')
            if category not in categories[i].split('|'):categories[i]+='|'+category
            return
        seen[key]=len(cases);cases.append({'args':args,'expected':result,'compare':'return'});categories.append(category)
    for c in public_examples(pid,raw):add(c['args'],'pinned-public-example',c['expected'])
    if pid in (2920,2925):
        for n in range(2,6):
            for parents in product(*(range(i) for i in range(1,n))):
                edges=[[p,i] for i,p in enumerate(parents,1)]
                profiles=list(product((0,1,3) if pid==2920 else (1,2,3),repeat=n)) if n<=3 else [[v]*n for v in ((0,1,3) if pid==2920 else (1,2,3))]+[[(0,1,3)[i%3] if pid==2920 else i%3+1 for i in range(n)]]
                for values in profiles:
                    if pid==2920:
                        for k in (0,1,4):add([edges,list(values),k],'exhaustive-small-parent-trees-selected-value-profiles')
                    else:add([edges,list(values)],'exhaustive-small-parent-trees-selected-value-profiles')
        for _ in range(50):
            n=rng.randrange(2,11 if pid==2920 else 13);labels=list(range(1,n));rng.shuffle(labels);labels=[0]+labels
            edges=[[labels[rng.randrange(i)],labels[i]] for i in range(1,n)];rng.shuffle(edges)
            edges=[e[::-1] if rng.randrange(2) else e for e in edges]
            values=[rng.randrange(0 if pid==2920 else 1,10001 if pid==2920 else 10**9+1) for _ in range(n)]
            add([edges,values,rng.randrange(10001)] if pid==2920 else [edges,values],'seeded-relabeled-tree-mode-or-retention-subsets')
        n=50000 if pid==2920 else 20000
        chain=[[i-1,i] for i in range(1,n)];star=[[0,i] for i in range(1,n)];binary=[[(i-1)//2,i] for i in range(1,n)]
        if pid==2920:
            add([chain,[10000]*n,0],'analytic-large-chain-no-penalty',n*10000)
            add([star,[0]*n,10000],'analytic-large-star-zero-coins',0)
            add([binary,[1]*n,0],'analytic-large-balanced-tree-no-penalty',n)
            smallstar=[[0,i] for i in range(1,101)]
            add([smallstar,[10000]+[0]*100,10000],'analytic-root-halving-vs-negative-ordinary',5000)
        else:
            add([chain,[10**9]*n],'analytic-maximum-chain-retain-one-minimum',(n-1)*10**9)
            add([star,[1]*n],'analytic-maximum-star-retain-root',n-1)
            add([binary,[10**9]*n],'analytic-maximum-uniform-balanced-retain-root',(n-1)*10**9)
            add([star,[10**9]+[1]*(n-1)],'analytic-maximum-star-retain-all-leaves',10**9)
    elif pid==2967:
        for n in range(1,6):
            for values in product(range(1,6),repeat=n):add([list(values)],'exhaustive-small-positive-palindrome-targets')
        for _ in range(50):add([[rng.randrange(1,1001) for _ in range(rng.randrange(1,9))]],'seeded-bounded-palindrome-enumeration')
        for v in (9,10,11,99,100,101,999,1000):add([[v]],'decimal-length-and-palindrome-boundaries')
        for a,want in [([10**9],1),([10**9]*7,7),([999999998,10**9],2),([1,10**9],999999999)]:add([a],'analytic-separate-numeric-maximum-unrestricted-positive-target',want)
        add([[11]*100000],'analytic-maximum-length-palindrome',0)
        add([[999999999]*100000],'analytic-fitting-near-maximum-numeric-palindrome',0)
        add([[1]*50000+[99999]*50000],'analytic-maximum-even-median-interval',50000*99998)
    else:
        for n in range(1,8):
            for values in product((1,2,3),repeat=n):add([list(values)],'exhaustive-strict-increasing-remainder')
        for _ in range(60):add([[rng.randrange(1,10**9+1) for _ in range(rng.randrange(1,61))]],'seeded-full-value-range-removals')
        for a in ([1],[10**9],[1,1],[1,2],[2,1],[999999999,10**9]):add([a],'strict-equality-singleton-numeric-boundary')
        n=100000
        add([list(range(1,n+1))],'analytic-maximum-increasing',n*(n+1)//2)
        add([list(range(n,0,-1))],'analytic-maximum-decreasing',3)
        add([[1000000]*n],'analytic-maximum-flat',3)
        add([list(range(2,n+1))+[1]],'analytic-maximum-trailing-minimum',n+1)
    return cases,categories


def expected_observation_bytes(batch,language):
    if language not in ('javascript','python'):raise ValueError('unsupported language')
    return sum(len(q.encoded({'i':i,'result':c['expected'],'result_type':q.expected_type(c['expected'],language),'args_before':c['args'],'args_after':c['args'],'alias_edges':[]})) for i,c in enumerate(batch))+len(q.encoded({'done':len(batch)}))+(language=='python')


def build_cases(pid,raw):
    cases,categories=_generate_cases(pid,raw)
    if len(cases)!=CASE_COUNT.get(pid) or q.sha(q.encoded(cases))!=CASES_SHA256.get(pid):raise ValueError('frozen case identity mismatch')
    if len(q.encoded(cases))>q.MAX_FILE:raise ValueError('case file cap exceeded')
    for _,batch in q.batches(cases):
        if any(expected_observation_bytes(batch,lang)>q.LIMITS['max_output_bytes'] for lang in ('javascript','python')):raise ValueError('output cap exceeded')
    return cases,categories
