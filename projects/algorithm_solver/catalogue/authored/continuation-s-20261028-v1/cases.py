"""Bounded source-free S case generators; no candidate loader."""
import importlib.util
import json
from pathlib import Path
from itertools import product
import random
S=importlib.util.spec_from_file_location('gamma_s_cases_oracles',Path(__file__).with_name('oracles.py'));oracle=importlib.util.module_from_spec(S);S.loader.exec_module(oracle)
IDS=oracle.IDS

def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def linked(values):return {'values':values,'next':[i+1 if i+1<len(values) else None for i in range(len(values))],'head':0 if values else None}
def complete(values):return {'values':values,'left':[2*i+1 if 2*i+1<len(values) else None for i in range(len(values))],'right':[2*i+2 if 2*i+2<len(values) else None for i in range(len(values))],'root':0 if values else None}
def chain(n,left):return {'values':[i%201-100 for i in range(n)],'left':[i+1 if left and i+1<n else None for i in range(n)],'right':[i+1 if not left and i+1<n else None for i in range(n)],'root':0 if n else None}
def build_cases():
    data={pid:[] for pid in IDS};seen={pid:set() for pid in IDS};rng=random.Random(2026102830)
    def add(pid,args,tag):
        raw=encoded(args)
        if raw in seen[pid]:return
        seen[pid].add(raw);data[pid].append({'args':args,'expected':oracle.expected(pid,args),'category':tag})
    for n in range(31):add(199,[complete([i%3-1 for i in range(n)])],'smallcomplete-rightview')
    for left in (False,True):add(199,[chain(100,left)],'maximum-depth-rightview')
    for _ in range(48):
        n=rng.randrange(1,101);p=complete([rng.randint(-100,100) for _ in range(n)])
        for i in range(n):
            if rng.randrange(2):p['left'][i],p['right'][i]=p['right'][i],p['left'][i]
        add(199,[p],'seeded-shape-rightview')
    for n in range(6):
        for values in product((1,2),repeat=n):
            for val in (0,1,2,50):add(203,[linked(list(values)),val],'exhaustive-small-list-filter')
        for values in product((-1,1),repeat=n):add(206,[linked(list(values))],'exhaustive-small-reverse')
    add(203,[linked([1,2]*5000),1],'maximum10000-original-identities');add(203,[linked([50]*10000),50],'maximum-all-removed');add(206,[linked([i-2500 for i in range(5000)])],'maximum5000-reversal')
    for pid in (203,206):
        for _ in range(32):
            n=rng.randint(1,40);order=rng.sample(range(n),n);values=[rng.randint(1,50) if pid==203 else rng.randint(-5000,5000) for _ in range(n)];nexts=[None]*n
            for i,j in zip(order,order[1:]):nexts[i]=j
            packet={'values':values,'next':nexts,'head':order[0]}
            add(pid,[packet,rng.randint(0,50)] if pid==203 else [packet],'seeded-permuted-original-identity-pool')
    for pid in (208,211):
        name=oracle.CLASSES[pid];insert='insert' if pid==208 else 'addWord'
        for _ in range(32):
            ops=[name];rows=[[]]
            for _ in range(35):
                word=''.join(rng.choice('abc') for _ in range(rng.randint(1,5)))
                if rng.randrange(3)==0:op=insert
                elif pid==208:op=rng.choice(('search','startsWith'))
                else:
                    op='search';chars=list(word)
                    for i in rng.sample(range(len(chars)),rng.randint(0,min(2,len(chars)))):chars[i]='.'
                    word=''.join(chars)
                ops.append(op);rows.append([word])
            add(pid,[ops,rows],'seeded-native-state')
        maximum=2000 if pid==208 else 25;word='a'*maximum
        query='startsWith' if pid==208 else 'search'
        add(pid,[[name,insert,insert,'search',query],[[],[word],[word],[word],[word if pid==208 else '.'+word[1:-1]+'.']]],'maximum-word-and-duplicate-insert')
        calls=30000 if pid==208 else 10000
        add(pid,[[name,insert]+['search']*(calls-1),[[],['a']]+[['a']]*(calls-1)],'maximum-callcount-bounded-state')
    words=[''.join(p) for n in range(1,5) for p in product('ab',repeat=n)]
    for chars in product('ab',repeat=4):add(212,[[list(chars[:2]),list(chars[2:])],words],'exhaustive-two-by-two-binary-words')
    add(212,[[['a']*12 for _ in range(12)],['a'*n for n in range(1,11)]],'maximum-board-wordlength')
    def alphabetic(i):
        text=''
        while True:
            text=chr(97+i%26)+text;i//=26
            if not i:return text
    add(212,[[['a']],['a']+['b'+alphabetic(i) for i in range(29999)]],'maximum30000-distinct-words')
    add(212,[[list('oaan'),list('etae'),list('ihkr'),list('iflv')],['oath','pea','eat','rain']],'public-board-example')
    for n in range(7):
        for chars in product('abc',repeat=n):add(214,[''.join(chars)],'exhaustive-small-shortest-palindrome')
    for s in ('a'*50000,'a'*49999+'b','ab'*25000):add(214,[s],'maximum-length-shortest-palindrome')
    for n in list(range(129))+[255,256,257,1023,1024,1025,32767,32768,50000]:add(222,[complete([i%50001 for i in range(n)])],'complete-count-boundary')
    expressions=['1 + 1',' 2-1 + 2 ','(1+(4+5+2)-3)+(6+8)','-(2+3)','1-(-2)','-(-(-1))','0','2147483647','(-2147483647)-1']
    def expression(depth):
        if depth==0 or rng.randrange(3)==0:return str(rng.randrange(101))
        left,right=expression(depth-1),expression(depth-1);text='(('+left+')'+rng.choice('+-')+'('+right+'))'
        return '-('+text+')' if rng.randrange(4)==0 else text
    expressions += [expression(4) for _ in range(256)]
    expressions += ['1+'*149999+'1','('*149999+'1'+')'*149999,'(-'*99999+'1'+')'*99999]
    for s in expressions:add(224,[s],'grammar-and-depth-expression')
    for n in range(7):
        for choices in product(('push','pop'),repeat=n):
            ops=['MyStack'];rows=[[]];size=0
            for name in choices:
                if name=='pop' and not size:break
                ops.append(name);rows.append([size%2+1] if name=='push' else []);size+=1 if name=='push' else -1
                ops.append('empty');rows.append([])
                if size:ops.append('top');rows.append([])
            else:add(225,[ops,rows],'exhaustive-valid-small-queue-stack')
    for _ in range(48):
        ops=['MyStack'];rows=[[]];size=0
        for _ in range(100):
            name=rng.choice(('push','pop','top','empty')) if size else rng.choice(('push','empty'))
            ops.append(name);rows.append([rng.randint(1,9)] if name=='push' else []);size+=(name=='push')-(name=='pop')
        add(225,[ops,rows],'maximum100-valid-stack-calls')
    return data
