"""Statement-domain admission for historical cases whose executions were clean.

Admission uses inputs only, never the candidate output or historical expectation.
Every excluded vector remains in the run's rejection ledger. Problem statements
are pinned in the freeze; this module grants no qualification by itself.
"""
from collections import Counter, deque
from datetime import date
from math import gcd
import string
import re

LOWER = string.ascii_lowercase
LETTERS = string.ascii_letters
DIGITS = string.digits


def integer(x, lo, hi):
    return type(x) is int and lo <= x <= hi


def array(x, minimum, maximum, check):
    return type(x) is list and minimum <= len(x) <= maximum and all(check(v) for v in x)


def ints(x, lo, hi, minimum=1, maximum=100000):
    return array(x, minimum, maximum, lambda v: integer(v, lo, hi))


def text(x, alphabet=LOWER, minimum=1, maximum=100000):
    return type(x) is str and minimum <= len(x) <= maximum and set(x) <= set(alphabet)


def words(x, alphabet=LOWER, minimum=1, maximum=100000, width=100):
    return array(x, minimum, maximum, lambda w: text(w, alphabet, 1, width))


def spaced(x, alphabet=LOWER, maximum=100000):
    return text(x, alphabet+' ', 1, maximum) and all(x.split(' '))


def matrix(x, lo, hi, minimum=1, maximum=100, columns=None):
    return (type(x) is list and minimum <= len(x) <= maximum and type(x[0]) is list
            and minimum <= len(x[0]) <= (maximum if columns is None else columns)
            and all(ints(row, lo, hi, len(x[0]), len(x[0])) for row in x))


def unique(x):
    return len(set(x)) == len(x)


def increasing(x):
    return all(a < b for a, b in zip(x, x[1:]))


def rows(x, width, lo, hi, minimum=1, maximum=100000):
    return array(x, minimum, maximum, lambda row: ints(row, lo, hi, width, width))


def graph(n, edges, *, tree=False, dag=False, base=0):
    if not rows(edges, 2, base, n-1+base, 0, n*(n-1)//2):
        return False
    if any(a == b for a, b in edges) or not unique([tuple(e) if dag else tuple(sorted(e)) for e in edges]):
        return False
    adj = [[] for _ in range(n)]; indegree = [0]*n
    for a, b in edges:
        a -= base; b -= base; adj[a].append(b); indegree[b] += 1
        if tree: adj[b].append(a)
    if tree:
        if len(edges) != n-1: return False
        seen = {0}; queue = [0]
        for v in queue:
            for w in adj[v]:
                if w not in seen: seen.add(w); queue.append(w)
        return len(seen) == n
    if dag:
        queue = deque(i for i, d in enumerate(indegree) if d == 0); seen = 0
        while queue:
            v = queue.popleft(); seen += 1
            for w in adj[v]:
                indegree[w] -= 1
                if indegree[w] == 0: queue.append(w)
        return seen == n
    return True


def islands(grid):
    unseen = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v}
    count = 0
    while unseen:
        count += 1; stack = [unseen.pop()]
        while stack:
            r,c = stack.pop()
            for point in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)):
                if point in unseen: unseen.remove(point); stack.append(point)
    return count


def prefixed_balance(s, positive, negative):
    count = 0
    for c in s:
        count += (c in positive) - (c in negative)
        if count < 0: return False
    return True


# Exact one-argument contracts: bounds are values then array/string lengths.
SCALARS = {552:(1,100000),1359:(1,500),1399:(1,10000),1411:(1,5000),1510:(1,100000),
           1553:(1,2*10**9),1680:(1,100000),1688:(1,200),2180:(1,1000),2318:(1,10000),
           2413:(1,150),2485:(1,1000),2595:(1,1000),2652:(1,1000),2729:(100,999),
           2806:(0,100),3099:(1,100)}
ARRAYS = {
    1295:(1,100000,1,500),1299:(1,100000,1,10000),1345:(-10**8,10**8,1,50000),
    1354:(1,10**9,1,50000),1363:(0,9,1,10000),1406:(-1000,1000,1,50000),
    1426:(0,1000,1,1000),1480:(-10**6,10**6,1,1000),1502:(-10**6,10**6,2,1000),
    1509:(-10**9,10**9,1,100000),1550:(1,1000,1,1000),1563:(1,10**6,1,500),
    1608:(0,1000,1,100),1664:(1,10000,1,100000),1675:(1,10**9,2,50000),
    1995:(1,100,4,50),2036:(-100000,100000,1,100000),2121:(1,100000,1,100000),
    2164:(1,100,1,100),2198:(1,100,3,100000),2210:(1,100,3,100),2244:(1,10**9,1,100000),
    2436:(2,10**9,1,2000),2460:(0,1000,2,2000),2495:(1,100000,1,100000),
    2511:(-1,1,1,1000),2574:(1,100000,1,1000),2588:(0,10**6,1,100000),
    2601:(1,1000,1,1000),2615:(0,10**9,1,100000),2815:(1,10000,2,100),
    2870:(1,10**6,2,100000),2932:(1,100,1,50),2951:(1,100,3,100),2960:(0,100,1,100),
    2970:(1,50,1,50),2980:(1,100,2,100),3010:(1,50,3,50),3024:(1,100,3,3),
    3038:(1,1000,2,100),3151:(1,100,1,100),3184:(1,10**9,1,100),3190:(1,50,1,50)}
STRINGS = {
    1312:(LOWER,1,500),1320:(LETTERS[26:],2,300),1371:(LOWER,1,500000),
    1422:('01',2,500),1496:('NSEW',1,10000),1541:('()',1,100000),1544:(LETTERS,1,100),
    1702:('01',1,100000),1758:('01',1,10000),1805:(LOWER+DIGITS,1,1000),1832:(LOWER,1,1000),
    1864:('01',1,1000),1930:(LOWER,3,100000),2063:(LOWER,1,100000),2264:(DIGITS,3,1000),
    2405:(LOWER,1,100000),2414:(LOWER,1,100000),2609:('01',1,50),2697:(LOWER,1,1000),
    2716:(LOWER,1,100),2833:('LR_',1,50),3019:(LETTERS,1,100),3090:(LOWER,2,100),
    3110:(LOWER,2,100),3136:(LETTERS+DIGITS+'@#$',1,20),3216:(DIGITS,2,100)}
MATRICES = {861:(0,1,1,20),1284:(0,1,1,3),1368:(1,4,1,100),1463:(0,100,2,70),
            1504:(0,1,1,150),1568:(0,1,1,30),1591:(1,60,1,60),1632:(-10**9,10**9,1,500),
            2643:(0,1,1,100)}


def validate(pid, args):
    if type(args) is not list:
        raise ValueError(f'{pid}: ordered JSON arguments required')
    a = args
    good = False
    try:
        if pid in SCALARS: good = len(a)==1 and integer(a[0],*SCALARS[pid])
        elif pid in ARRAYS: good = len(a)==1 and ints(a[0],*ARRAYS[pid])
        elif pid in STRINGS: good = len(a)==1 and text(a[0],*STRINGS[pid])
        elif pid in MATRICES: good = len(a)==1 and matrix(a[0],*MATRICES[pid])
        elif pid==282: good=len(a)==2 and text(a[0],DIGITS,1,10) and integer(a[1],-2**31,2**31-1)
        elif pid==691: good=len(a)==2 and words(a[0],maximum=50,width=10) and text(a[1],maximum=15)
        elif pid==809: good=len(a)==2 and text(a[0],maximum=100) and words(a[1],maximum=100)
        elif pid==873: good=len(a)==1 and ints(a[0],1,10**9,3,1000) and increasing(a[0])
        elif pid==884: good=len(a)==2 and all(spaced(s,maximum=200) for s in a)
        elif pid==904: good=len(a)==1 and ints(a[0],0,len(a[0])-1)
        elif pid==934: good=len(a)==1 and matrix(a[0],0,1,2,100) and len(a[0])==len(a[0][0]) and islands(a[0])==2
        elif pid==936: good=len(a)==2 and text(a[1],maximum=1000) and text(a[0],maximum=len(a[1]))
        elif pid==956: good=len(a)==1 and ints(a[0],1,1000,1,20) and sum(a[0])<=5000
        elif pid==1235:
            start,end,profit=a; n=len(start); good=ints(start,1,10**9,1,50000) and ints(end,1,10**9,n,n) and ints(profit,1,10000,n,n) and all(s<e for s,e in zip(start,end))
        elif pid==1240: good=len(a)==2 and all(integer(v,1,13) for v in a)
        elif pid==1257:
            regions,r1,r2=a
            good=array(regions,2,10000,lambda row: words(row,LETTERS+' ',2,20,20)) and text(r1,LETTERS+' ',maximum=20) and text(r2,LETTERS+' ',maximum=20) and r1!=r2
            if good:
                parents={}; nodes=set()
                for row in regions:
                    nodes.update(row)
                    for child in row[1:]:
                        if child in parents and parents[child]!=row[0]: good=False
                        parents[child]=row[0]
                roots=nodes-set(parents); good=good and len(roots)==1 and r1 in nodes and r2 in nodes
                if good:
                    for node in nodes:
                        seen=set()
                        while node in parents and node not in seen: seen.add(node); node=parents[node]
                        if node not in roots: good=False; break
        elif pid==1269: good=len(a)==2 and integer(a[0],1,500) and integer(a[1],1,10**6)
        elif pid==1276: good=len(a)==2 and all(integer(v,0,10**7) for v in a)
        elif pid==1290: good=len(a)==1 and type(a[0])is dict and set(a[0])=={'__list_node__'} and ints(a[0]['__list_node__'],0,1,1,30)
        elif pid==1298:
            status,candies,keys,boxes,initial=a; n=len(status)
            good=ints(status,0,1,1,1000) and ints(candies,1,1000,n,n) and array(keys,n,n,lambda row: ints(row,0,n-1,0,n) and unique(row)) and array(boxes,n,n,lambda row: ints(row,0,n-1,0,n) and unique(row)) and ints(initial,0,n-1,0,n)
            if good: good=unique([v for row in boxes for v in row])
        elif pid==1307: good=len(a)==2 and words(a[0],LETTERS[26:],2,5,7) and text(a[1],LETTERS[26:],1,7) and len(set(''.join(a[0])+a[1]))<=10
        elif pid==1318: good=len(a)==3 and all(integer(v,1,10**9) for v in a)
        elif pid==1326: good=len(a)==2 and integer(a[0],1,10000) and ints(a[1],0,100,a[0]+1,a[0]+1)
        elif pid==1333:
            restaurants,vegan,price,distance=a
            good=rows(restaurants,5,0,100000,1,10000) and integer(vegan,0,1) and integer(price,1,100000) and integer(distance,1,100000) and unique([r[0]for r in restaurants]) and all(r[0]>=1 and r[1]>=1 and r[2]in(0,1) and r[3]>=1 and r[4]>=1 for r in restaurants)
        elif pid==1334:
            n,edges,threshold=a;good=integer(n,2,100) and rows(edges,3,0,10000,1,n*(n-1)//2) and integer(threshold,1,10000) and all(0<=s<t<n and w>=1 for s,t,w in edges) and unique([(s,t)for s,t,w in edges])
        elif pid==1340: good=len(a)==2 and ints(a[0],1,100000,1,1000) and integer(a[1],1,len(a[0]))
        elif pid==1349: good=len(a)==1 and array(a[0],1,8,lambda row: array(row,1,8,lambda c: type(c)is str and c in('.','#'))) and len({len(r)for r in a[0]})==1
        elif pid==1360: good=len(a)==2 and all(type(v)is str and re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',v) is not None and date(1971,1,1)<=date.fromisoformat(v)<=date(2100,12,31) for v in a)
        elif pid==1361:
            n,left,right=a;good=integer(n,1,10000) and ints(left,-1,n-1,n,n) and ints(right,-1,n-1,n,n)
        elif pid==1380: good=len(a)==1 and matrix(a[0],1,100000,1,50) and unique([v for r in a[0]for v in r])
        elif pid==1387: good=len(a)==3 and integer(a[0],1,1000) and integer(a[1],a[0],1000) and integer(a[2],1,a[1]-a[0]+1)
        elif pid==1388: good=len(a)==1 and ints(a[0],1,1000,1,500) and len(a[0])%3==0
        elif pid==1401:
            radius,xc,yc,x1,y1,x2,y2=a;good=integer(radius,1,2000) and all(integer(v,-10000,10000)for v in a[1:]) and x1<x2 and y1<y2
        elif pid==1404: good=len(a)==1 and text(a[0],'01',1,500) and a[0][0]=='1'
        elif pid==1416: good=len(a)==2 and text(a[0],DIGITS) and (len(a[0])==1 or a[0][0]!='0') and integer(a[1],1,10**9)
        elif pid==1425: good=len(a)==2 and ints(a[0],-10000,10000) and integer(a[1],1,len(a[0]))
        elif pid==1431: good=len(a)==2 and ints(a[0],1,100,2,100) and integer(a[1],1,50)
        elif pid==1436:
            paths=a[0];good=len(a)==1 and array(paths,1,100,lambda row: words(row,LETTERS+' ',2,2,10) and row[0]!=row[1])
            if good:
                starts=[r[0]for r in paths];ends=[r[1]for r in paths];good=unique(starts) and unique(ends) and len(set(starts)-set(ends))==1
                if good:
                    links=dict(paths);node=next(iter(set(starts)-set(ends)));seen=set()
                    while node in links and node not in seen:seen.add(node);node=links[node]
                    good=len(seen)==len(paths) and node not in links
        elif pid==1449: good=len(a)==2 and ints(a[0],1,5000,9,9) and integer(a[1],1,5000)
        elif pid==1465:
            h,w,hc,vc=a;good=integer(h,2,10**9) and integer(w,2,10**9) and ints(hc,1,h-1,1,min(h-1,100000)) and ints(vc,1,w-1,1,min(w-1,100000)) and unique(hc) and unique(vc)
        elif pid==1473:
            houses,cost,m,n,target=a;good=integer(m,1,100) and integer(n,1,20) and integer(target,1,m) and ints(houses,0,n,m,m) and array(cost,m,m,lambda r:ints(r,1,10000,n,n))
        elif pid==1478: good=len(a)==2 and ints(a[0],1,10000,1,100) and unique(a[0]) and integer(a[1],1,len(a[0]))
        elif pid==1494:
            n,edges,k=a;good=integer(n,1,15) and integer(k,1,n) and graph(n,edges,dag=True,base=1)
        elif pid==1499:
            points,k=a;good=rows(points,2,-10**8,10**8,2,100000) and increasing([r[0]for r in points]) and integer(k,0,2*10**8) and any(q[0]-p[0]<=k for p,q in zip(points,points[1:]))
        elif pid==1503:
            n,left,right=a;good=integer(n,1,10000) and ints(left,0,n,0,n+1) and ints(right,0,n,0,n+1) and 1<=len(left)+len(right)<=n+1 and unique(left+right)
        elif pid==1519:
            n,edges,labels=a;good=integer(n,1,100000) and text(labels,LOWER,n,n) and graph(n,edges,tree=True)
        elif pid==1531: good=len(a)==2 and text(a[0],maximum=100) and integer(a[1],0,len(a[0]))
        elif pid==1537: good=len(a)==2 and all(ints(xs,1,10**7) and increasing(xs)for xs in a)
        elif pid==1562: good=len(a)==2 and ints(a[0],1,len(a[0])) and unique(a[0]) and integer(a[1],1,len(a[0]))
        elif pid in (1564,1580): good=len(a)==2 and all(ints(xs,1,10**9)for xs in a)
        elif pid==1579:
            n,edges=a;good=integer(n,1,100000) and rows(edges,3,1,max(3,n),1,min(100000,3*n*(n-1)//2)) and all(1<=t<=3 and u<v<=n for t,u,v in edges) and unique([tuple(e)for e in edges])
        elif pid==1595: good=len(a)==1 and matrix(a[0],0,100,1,12) and len(a[0])>=len(a[0][0])
        elif pid==1659:
            m,n,ic,ec=a;good=integer(m,1,5) and integer(n,1,5) and integer(ic,0,min(m*n,6)) and integer(ec,0,min(m*n,6))
        elif pid==1665: good=len(a)==1 and rows(a[0],2,1,10000) and all(x<=y for x,y in a[0])
        elif pid==1668: good=len(a)==2 and all(text(s,maximum=100)for s in a)
        elif pid==1671:
            xs=a[0];good=len(a)==1 and ints(xs,1,10**9,3,1000)
            if good:
                left=[];small=10**9+1
                for x in xs:left.append(small<x);small=min(small,x)
                small=10**9+1;possible=False
                for i in range(len(xs)-1,-1,-1):possible|=left[i] and small<xs[i];small=min(small,xs[i])
                good=possible
        elif pid==1673: good=len(a)==2 and ints(a[0],0,10**9) and integer(a[1],1,len(a[0]))
        elif pid==1691: good=len(a)==1 and rows(a[0],3,1,100,1,100)
        elif pid==1694: good=len(a)==1 and text(a[0],DIGITS+'- ',2,100) and sum(c in DIGITS for c in a[0])>=2
        elif pid==1697:
            n,edges,queries=a;good=integer(n,2,100000) and all(rows(xs,3,0,10**9) and all(u<n and v<n and u!=v and w>=1 for u,v,w in xs)for xs in(edges,queries))
        elif pid==1707: good=len(a)==2 and ints(a[0],0,10**9) and rows(a[1],2,0,10**9)
        elif pid==1727: good=len(a)==1 and matrix(a[0],0,1,1,100000) and len(a[0])*len(a[0][0])<=100000
        elif pid==1742: good=len(a)==2 and integer(a[0],1,100000) and integer(a[1],a[0],100000)
        elif pid==1772: good=len(a)==2 and words(a[0],maximum=10000,width=10) and unique(a[0]) and array(a[1],1,100,lambda s:spaced(s,maximum=1000))
        elif pid==1784: good=len(a)==1 and text(a[0],'01',1,100) and a[0][0]=='1'
        elif pid==1788: good=len(a)==1 and ints(a[0],-10000,10000,2,100000) and len(set(a[0]))<len(a[0])
        elif pid==1802: good=len(a)==3 and integer(a[0],1,10**9) and integer(a[1],0,a[0]-1) and integer(a[2],a[0],10**9)
        elif pid==1812: good=len(a)==1 and type(a[0])is str and len(a[0])==2 and a[0][0]in'abcdefgh' and a[0][1]in'12345678'
        elif pid==1852: good=len(a)==2 and ints(a[0],1,100000) and integer(a[1],1,len(a[0]))
        elif pid==1886: good=len(a)==2 and all(matrix(x,0,1,1,10) and len(x)==len(x[0])for x in a) and len(a[0])==len(a[1])
        elif pid==1905: good=len(a)==2 and all(matrix(x,0,1,1,500)for x in a) and len(a[0])==len(a[1]) and len(a[0][0])==len(a[1][0])
        elif pid==1927: good=len(a)==1 and text(a[0],DIGITS+'?',2,100000) and len(a[0])%2==0
        elif pid==1936: good=len(a)==2 and ints(a[0],1,10**9) and increasing(a[0]) and integer(a[1],1,10**9)
        elif pid==1945: good=len(a)==2 and text(a[0],maximum=100) and integer(a[1],1,10)
        elif pid==1985: good=len(a)==2 and words(a[0],DIGITS,1,10000,100) and all(len(s)==1 or s[0]!='0'for s in a[0]) and integer(a[1],1,len(a[0]))
        elif pid==2023: good=len(a)==2 and words(a[0],DIGITS,2,100,100) and all(len(s)==1 or s[0]!='0'for s in a[0]) and text(a[1],DIGITS,2,100) and a[1][0]!='0'
        elif pid==2047: good=len(a)==1 and text(a[0],LOWER+DIGITS+' -!.,',1,1000) and bool(a[0].split())
        elif pid==2061: good=len(a)==1 and matrix(a[0],0,1,1,300) and a[0][0][0]==0
        elif pid==2077: good=len(a)==2 and integer(a[0],2,1000) and rows(a[1],2,1,a[0],1,50000) and graph(a[0],a[1],base=1)
        elif pid==2078: good=len(a)==1 and ints(a[0],0,100,2,100) and len(set(a[0]))>=2
        elif pid==2125: good=len(a)==1 and words(a[0],'01',1,500,500) and len({len(s)for s in a[0]})==1
        elif pid==2154: good=len(a)==2 and ints(a[0],1,1000,1,1000) and integer(a[1],1,1000)
        elif pid in (2176,2656,2760): good=len(a)==2 and ints(a[0],1,100,1,100) and integer(a[1],1,100)
        elif pid==2182: good=len(a)==2 and text(a[0]) and integer(a[1],1,len(a[0]))
        elif pid==2187: good=len(a)==2 and ints(a[0],1,10**7) and integer(a[1],1,10**7)
        elif pid==2206: good=len(a)==1 and ints(a[0],1,500,2,1000) and len(a[0])%2==0
        elif pid==2207: good=len(a)==2 and text(a[0]) and text(a[1],LOWER,2,2)
        elif pid==2217: good=len(a)==2 and ints(a[0],1,10**9,1,50000) and integer(a[1],1,15)
        elif pid==2225: good=len(a)==1 and rows(a[0],2,1,100000) and all(x!=y for x,y in a[0]) and unique([tuple(r)for r in a[0]])
        elif pid==2236: good=len(a)==1 and type(a[0])is dict and set(a[0])=={'__tree_node__'} and ints(a[0]['__tree_node__'],-100,100,3,3)
        elif pid==2240: good=len(a)==3 and all(integer(v,1,10**6)for v in a)
        elif pid==2255: good=len(a)==2 and words(a[0],maximum=1000,width=10) and text(a[1],maximum=10)
        elif pid==2278: good=len(a)==2 and text(a[0],maximum=100) and text(a[1],LOWER,1,1)
        elif pid==2297: good=len(a)==2 and ints(a[0],0,100000) and ints(a[1],0,100000,len(a[0]),len(a[0]))
        elif pid==2315: good=len(a)==1 and text(a[0],LOWER+'|*',1,1000) and a[0].count('|')%2==0
        elif pid==2323: good=len(a)==2 and ints(a[0],1,100000) and ints(a[1],1,100000,len(a[0]),len(a[0]))
        elif pid==2374: good=len(a)==1 and ints(a[0],0,len(a[0])-1,2,100000) and all(i!=v for i,v in enumerate(a[0]))
        elif pid==2392: good=len(a)==3 and integer(a[0],2,400) and all(rows(xs,2,1,a[0],1,10000) and all(x!=y for x,y in xs)for xs in a[1:])
        elif pid==2418: good=len(a)==2 and words(a[0],LETTERS,1,1000,20) and ints(a[1],1,100000,len(a[0]),len(a[0])) and unique(a[1])
        elif pid==2441: good=len(a)==1 and ints(a[0],-1000,1000,1,1000) and 0 not in a[0]
        elif pid==2489: good=len(a)==3 and text(a[0],'01') and integer(a[1],1,len(a[0])) and integer(a[2],1,len(a[0])) and gcd(a[1],a[2])==1
        elif pid==2490: good=len(a)==1 and spaced(a[0],LETTERS,500)
        elif pid==2496: good=len(a)==1 and words(a[0],LOWER+DIGITS,1,100,9)
        elif pid==2497:
            vals,edges,k=a;n=len(vals);good=ints(vals,-10000,10000) and rows(edges,2,0,n-1,0,min(n*(n-1)//2,100000)) and all(u!=v for u,v in edges) and integer(k,0,n-1)
        elif pid==2512:
            pos,neg,reports,ids,k=a;n=len(reports);good=words(pos,maximum=10000) and words(neg,maximum=10000) and not(set(pos)&set(neg)) and array(reports,1,10000,lambda s:text(s,LOWER+' ',1,100) and '  'not in s.strip(' ')) and ints(ids,1,10**9,n,n) and unique(ids) and integer(k,1,n)
        elif pid==2525: good=len(a)==4 and all(integer(v,1,100000)for v in a[:3]) and integer(a[3],1,1000)
        elif pid==2529: good=len(a)==1 and ints(a[0],-2000,2000,1,2000) and a[0]==sorted(a[0])
        elif pid==2531: good=len(a)==2 and all(text(s)for s in a)
        elif pid==2558: good=len(a)==2 and ints(a[0],1,10**9,1,1000) and integer(a[1],1,1000)
        elif pid==2611: good=len(a)==3 and ints(a[0],1,1000) and ints(a[1],1,1000,len(a[0]),len(a[0])) and integer(a[2],0,len(a[0]))
        elif pid==2614: good=len(a)==1 and matrix(a[0],1,4*10**6,1,300) and len(a[0])==len(a[0][0])
        elif pid==2660: good=len(a)==2 and ints(a[0],0,10,1,1000) and ints(a[1],0,10,len(a[0]),len(a[0]))
        elif pid==2682: good=len(a)==2 and integer(a[0],1,50) and integer(a[1],1,a[0])
        elif pid==2706: good=len(a)==2 and ints(a[0],1,100,2,50) and integer(a[1],1,100)
        elif pid==2717: good=len(a)==1 and ints(a[0],1,50,2,50) and sorted(a[0])==list(range(1,len(a[0])+1))
        elif pid==2748: good=len(a)==1 and ints(a[0],1,9999,2,100) and all(v%10!=0 for v in a[0])
        elif pid==2763: good=len(a)==1 and ints(a[0],1,len(a[0]),1,1000)
        elif pid==2788: good=len(a)==2 and words(a[0],LOWER+'.,|$#@',1,100,20) and text(a[1],'.,|$#@',1,1)
        elif pid==2824: good=len(a)==2 and ints(a[0],-50,50,1,50) and integer(a[1],-50,50)
        elif pid==2838: good=len(a)==3 and ints(a[0],1,10**9) and ints(a[1],1,10**9) and ints(a[2],1,10**9,len(a[1]),len(a[1]))
        elif pid==2843: good=len(a)==2 and integer(a[0],1,10000) and integer(a[1],a[0],10000)
        elif pid==2859: good=len(a)==2 and ints(a[0],1,100000,1,1000) and integer(a[1],0,10)
        elif pid==2894: good=len(a)==2 and all(integer(v,1,1000)for v in a)
        elif pid==2928: good=len(a)==2 and all(integer(v,1,50)for v in a)
        elif pid==2974: good=len(a)==1 and ints(a[0],1,100,2,100) and len(a[0])%2==0
        elif pid==3000: good=len(a)==1 and rows(a[0],2,1,100,1,100)
        elif pid==3007: good=len(a)==2 and integer(a[0],1,10**15) and integer(a[1],1,8)
        elif pid==3014: good=len(a)==1 and text(a[0],LOWER,1,26) and unique(a[0])
        elif pid==3028: good=len(a)==1 and ints(a[0],-10,10,1,100) and 0 not in a[0]
        elif pid==3033: good=len(a)==1 and matrix(a[0],-1,100,2,50) and all(max(col)>=0 for col in zip(*a[0]))
        elif pid==3042: good=len(a)==1 and words(a[0],maximum=50,width=10)
        elif pid==3046: good=len(a)==1 and ints(a[0],1,100,1,100) and len(a[0])%2==0
        elif pid==3065: good=len(a)==2 and ints(a[0],1,10**9,1,50) and integer(a[1],1,10**9) and max(a[0])>=a[1]
        elif pid==3069: good=len(a)==1 and ints(a[0],1,100,3,50) and unique(a[0])
        elif pid==3095: good=len(a)==2 and ints(a[0],0,50,1,50) and integer(a[1],0,63)
        elif pid==3102: good=len(a)==1 and rows(a[0],2,1,10**8,3,100000)
        elif pid==3127: good=len(a)==1 and array(a[0],3,3,lambda row:array(row,3,3,lambda c:type(c)is str and c in('W','B')))
        elif pid==3131: good=len(a)==2 and ints(a[0],0,1000,1,100) and ints(a[1],0,1000,len(a[0]),len(a[0])) and len({y-x for x,y in zip(sorted(a[0]),sorted(a[1]))})==1
        elif pid==3146: good=len(a)==2 and text(a[0],LOWER,1,26) and unique(a[0]) and type(a[1])is str and sorted(a[0])==sorted(a[1])
        elif pid==3149: good=len(a)==1 and ints(a[0],0,len(a[0])-1,2,14) and unique(a[0])
        elif pid==3161:
            qs=a[0];good=len(a)==1 and array(qs,1,150000,lambda r:ints(r,1,min(50000,3*len(qs)),2,3) and r[0]in(1,2) and len(r)==r[0]+1)
            if good:
                obstacles=set();good=any(r[0]==2 for r in qs)
                for r in qs:
                    if r[0]==1:
                        if r[1]in obstacles:good=False
                        obstacles.add(r[1])
        elif pid==3162: good=len(a)==3 and ints(a[0],1,50,1,50) and ints(a[1],1,50,1,50) and integer(a[2],1,50)
        elif pid==3168: good=len(a)==1 and text(a[0],'EL',1,50) and prefixed_balance(a[0],'E','L')
        elif pid==3174: good=len(a)==1 and text(a[0],LOWER+DIGITS,1,100) and prefixed_balance(a[0],LOWER,DIGITS)
        elif pid==3176: good=len(a)==2 and ints(a[0],1,10**9,1,500) and integer(a[1],0,min(len(a[0]),25))
        elif pid==3178: good=len(a)==2 and integer(a[0],2,50) and integer(a[1],1,50)
        elif pid in (3200,3222): good=len(a)==2 and all(integer(v,1,100)for v in a)
        elif pid==3224: good=len(a)==2 and integer(a[1],0,100000) and ints(a[0],0,a[1],2,100000) and len(a[0])%2==0
        elif pid==3226: good=len(a)==2 and all(integer(v,1,10**6)for v in a)
        elif pid==3238: good=len(a)==2 and integer(a[0],2,10) and rows(a[1],2,0,10,1,100) and all(x<a[0]for x,y in a[1])
        else: raise KeyError('unregistered clean problem')
    except (TypeError, ValueError, IndexError, KeyError, OverflowError):
        good=False
    if not good:
        raise ValueError(f'{pid}: outside pinned statement domain')
