"""Oracle-sized traces and maximum-boundary traces stay separate."""
from itertools import product, permutations
import random

def word(i):
    result = []
    for _ in range(5):
        result.append(chr(97+i%26));i//=26
    return ''.join(result)

def small_cases():
    choices = [('append',1),('append',100),('addAll',3),('multAll',2),('getIndex',0),('getIndex',3)]
    for choices4 in product(choices,repeat=4):
        yield 1622,[['Fancy']+[x[0] for x in choices4],[[]]+[[x[1]] for x in choices4]]
    rng = random.Random(24029)
    for _ in range(200):
        operations=['Fancy'];rows=[[]];length=0
        for _ in range(rng.randint(1,60)):
            operation=rng.choice(['append','addAll','multAll','getIndex']);operations.append(operation)
            if operation=='append':length+=1
            rows.append([rng.choice([0,max(0,length-1),length,100000]) if operation=='getIndex' else rng.choice([1,2,99,100])])
        yield 1622,[operations,rows]
    for n in range(1,7):
        for order in permutations(range(1,n+1)):
            yield 1656,[['OrderedStream']+['insert']*n,[[n]]+[[i,word(i)] for i in order]]
    for _ in range(100):
        n=rng.randint(7,30);order=rng.sample(range(1,n+1),n)
        yield 1656,[['OrderedStream']+['insert']*n,[[n]]+[[i,word(i)] for i in order]]

def boundary_cases():
    # Exactly 100000 calls; all outputs except the final query are void.
    yield 1622,[['Fancy','append']+['multAll']*99998+['getIndex'],[[],[100]]+[[100]]*99998+[[0]]],[None]*100000+[pow(100,99999,1000000007)],'Append 100 then multiply by 100 exactly 99998 times; closed form 100^99999 modulo prime.'
    yield 1622,[['Fancy']+['append']*50000+['addAll']*49999+['getIndex'],[[]]+[[100]]*50000+[[100]]*49999+[[49999]]],[None]*100000+[5000000],'All 50000 values start at 100 and gain 49999*100; exactly 100000 calls.'
    yield 1622,[['Fancy','getIndex'],[[],[100000]]],[None,-1],'Maximum index in an empty sequence is out of range.'
    for order in [list(range(1,1001)),list(range(1000,0,-1))]:
        expected=[None]+([[word(i)] for i in order] if order[0]==1 else [[] for _ in range(999)]+[[word(i) for i in range(1,1001)]])
        yield 1656,[['OrderedStream']+['insert']*1000,[[1000]]+[[i,word(i)] for i in order]],expected,'Maximum n=1000; increasing arrivals emit singleton chunks; reverse arrivals emit one complete sorted chunk at final insertion.'
