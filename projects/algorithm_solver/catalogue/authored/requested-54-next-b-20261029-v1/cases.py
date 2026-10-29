"""Small reference inputs and separate analytic boundaries."""
import random
from itertools import product
from oracles import best_free,TreeNode,encode_tree
IDS=[855,863,887,900,901]

def small_cases():
    rng=random.Random(54863901)
    for n in range(1,9):
        for _ in range(50):
            ops=['ExamRoom'];rows=[[n]];occupied=set()
            for step in range(25):
                if len(occupied)<n and (not occupied or rng.random()<.6):
                    ops.append('seat');rows.append([]);occupied.add(best_free(n,occupied))
                else:
                    seat=rng.choice(sorted(occupied));occupied.remove(seat);ops.append('leave');rows.append([seat])
            yield 855,[ops,rows]
    for n in range(1,30):
        for _ in range(5):
            values=rng.sample(range(501),n);nodes=[TreeNode(v) for v in values];slots=[(nodes[0],'left'),(nodes[0],'right')]
            for node in nodes[1:]:
                i=rng.randrange(len(slots));parent,side=slots.pop(i);setattr(parent,side,node);slots.extend([(node,'left'),(node,'right')])
            target=rng.choice(values)
            for k in [0,1,3,30]:yield 863,[encode_tree(nodes[0]),target,k]
    for k in range(1,7):
        for n in range(1,51):yield 887,[k,n]
    for counts in product(range(4),repeat=3):
        encoding=[counts[0],0,counts[1],1,counts[2],2]
        for calls in product([1,2],repeat=4):yield 900,[['RLEIterator']+['next']*4,[[encoding]]+[[v] for v in calls]]
    for n in range(1,7):
        for prices in product([1,2,3],repeat=n):yield 901,[['StockSpanner']+['next']*n,[[]]+[[p] for p in prices]]

def boundary_cases():
    # Domain maxima with closed-form expected answers; do not invoke reference().
    yield 855,[['ExamRoom']+['seat','leave']*5000,[[10**9]]+[v for _ in range(5000) for v in ([],[0])]], [None]+[v for _ in range(5000) for v in (0,None)],'Maximum room1e9 and10000 calls; each seat starts empty and returns0, followed by legal leave0.'
    yield 855,[['ExamRoom','seat','seat','seat'],[[10**9],[],[],[]]],[None,0,999999999,499999999],'Endpoint distances force0,last,then midpoint; lower tie chosen.'
    yield 863,[list(range(1,501)),1,8],list(range(256,501)),'Complete500-node tree; depth8 consists exactly of heap positions256..500.'
    yield 863,[list(range(1,501)),500,1000],[],'Any500-node tree has diameter<=499, so distance1000 is empty.'
    yield 887,[1,10000],10000,'One egg forces increasing-floor linear search.'
    yield 887,[2,10000],141,'Two-egg capacity afterm moves is m(m+1)/2;140 gives9870 and141 gives10011.'
    yield 887,[100,10000],14,'With at least14 eggs,14 binary decisions distinguish16384 floor thresholds, while13 distinguish only8192<10001.'
    encoding=[x for _ in range(500) for x in (10**9,10**9)]
    yield 900,[['RLEIterator']+['next']*1000,[[encoding]]+[[10**9]]*1000],[None]+[10**9]*500+[-1]*500,'All maximum1000 encoding elements and1000 calls;500 runs each exactly1e9 long, then exhausted.'
    yield 900,[['RLEIterator']+['next']*1000,[[[0,10**9]*500]]+[[10**9]]*1000],[None]+[-1]*1000,'Maximum zero-count run array encodes empty tape.'
    yield 901,[['StockSpanner']+['next']*10000,[[]]+[[100000]]*10000],[None]+list(range(1,10001)),'Maximum calls and maximum equal price: each span includes all previous equal prices.'
    yield 901,[['StockSpanner']+['next']*10000,[[]]+[[100000-i] for i in range(10000)]],[None]+[1]*10000,'Strict descending maximum-length quote stream gives span1 each time.'
