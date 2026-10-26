"""Independent statement-domain admission for the expanded 114-problem cohort.

Authored from pinned statement snapshots before inspecting candidate sources.
Historical cases stay immutable: every rejection and corrected expectation is
retained beside its original. Domain admission is not oracle verification or
qualification. Unsupported IDs fail closed. No candidate is executed here.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict, deque
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
import hashlib
import html
from itertools import combinations
import json
from math import gcd, isfinite, lcm
from pathlib import Path
import re
import string

from . import imported_case_admission as common

need, integer, array, numbers, text, matrix, arity = (
    common.need, common.integer, common.array, common.numbers,
    common.text, common.matrix, common.arity)
DomainError = common.DomainError
LOWER, UPPER, LETTERS = common.LOWER, common.UPPER, common.LETTERS
IDS = frozenset((171,190,191,205,231,258,263,405,448,461,1239,1275,1282,1304,
1310,1347,1376,1432,1447,1451,1456,1462,1491,1497,1583,1589,1604,1615,1616,
1619,1663,1700,1704,1721,1736,1738,1776,1792,1803,1829,1870,1916,1935,1946,
1963,1968,1970,1980,1986,1992,1994,2008,2024,2032,2040,2042,2064,2068,2087,
2097,2099,2115,2122,2133,2162,2163,2172,2193,2194,2197,2215,2218,2220,2224,
2249,2250,2273,2288,2293,2303,2306,2312,2317,2331,2334,2337,2343,2354,2368,
2376,2382,2402,2425,2429,2440,2458,2463,2465,2469,2470,2532,2544,2553,2561,
2570,2578,2584,2586,2589,2603,2646,2699,2732,2851))
DOMAIN_IDS = IDS
ORACLE_IDS = frozenset((171,190,191,205,231,258,263,405,448,461,1275,1310,1347,
1432,1447,1451,1456,1491,1497,1583,1604,1615,1616,1619,1663,1700,1704,1736,
1738,1829,1935,1946,1963,1992,1994,2024,2032,2042,2064,2068,2087,2115,2133,
2162,2194,2197,2215,2220,2224,2249,2273,2288,2293,2303,2306,2317,2331,2337,
2343,2354,2425,2429,2465,2469,2470,2544,2553,2570,2578,2586))
MOD = 10**9+7
COMPARISON_POLICIES = {
    1282:'partition-of-every-person-satisfying-group-sizes',1304:'n-distinct-integers-summing-to-zero',
    1447:'set-of-strings',1491:'finite-number-absolute-error-1e-5',
    1619:'finite-number-absolute-error-1e-5',1721:'list-values-with-declared-identity-effects',
    1776:'finite-number-vector-absolute-error-1e-5',1792:'finite-number-absolute-error-1e-5',
    1968:'permutation-with-no-neighbor-average',1980:'length-n-binary-string-not-in-input',
    1992:'set-of-coordinate-quadruples',2032:'set-of-integers',
    2097:'Euler-edge-arrangement-preserving-input-pairs',2099:'maximum-sum-length-k-subsequence',
    2115:'set-of-strings',2122:'positive-array-with-positive-integer-offset-recovering-input-multiset',
    2215:'ordered-pair-of-integer-sets',2303:'finite-number-absolute-error-1e-5',
    2334:'length-of-any-valid-subarray-or-proven-impossible',
    2469:'finite-number-vector-absolute-error-1e-5',
    2699:'modified-edge-list-with-preserved-fixed-weights-and-target-shortest-path-or-proven-impossible',
    2732:'sorted-distinct-good-row-subset-or-proven-impossible',
}


def numeric(value,lo,hi,name,decimal_places=None):
    need(type(value) in (int,float) and lo<=value<=hi and isfinite(value),
         f'{name} must be a finite number in [{lo}, {hi}]')
    if decimal_places is not None:
        scaled=Decimal(str(value))*10**decimal_places
        need(scaled==scaled.to_integral_value(),f'{name} has at most {decimal_places} decimal places')


def clock(value,name='time'):
    text(value,5,5,string.digits+':',name)
    need(re.fullmatch('[0-2][0-9]:[0-5][0-9]',value) is not None and int(value[:2])<24,
         f'{name} is a valid HH:MM time in [00:00,23:59]')
    return int(value[:2])*60+int(value[3:])


def sentence(value,lo,hi,alphabet,name):
    text(value,lo,hi,alphabet+' ',name)
    need(value==value.strip(' ') and '  ' not in value,f'{name} has single spaces and no leading/trailing spaces')
    return value.split(' ')


def unique_rows(rows,name):
    need(len({tuple(r) for r in rows})==len(rows),f'{name} rows are unique')


def words(values,nlo,nhi,wlo,whi,name,alphabet=LOWER,distinct=False):
    array(values,nlo,nhi,name)
    for value in values: text(value,wlo,whi,alphabet,f'{name}[i]')
    if distinct: need(len(set(values))==len(values),f'{name} strings are distinct')


def simple_graph(n,edges,connected=False,tree=False):
    array(edges,n-1 if tree else 0,n*(n-1)//2,'edges')
    if tree: need(len(edges)==n-1,'tree has exactly n-1 edges')
    parents=list(range(n));seen=set()
    def find(x):
        while parents[x]!=x: parents[x]=parents[parents[x]]; x=parents[x]
        return x
    for edge in edges:
        numbers(edge,2,2,0,n-1,'edge');u,v=edge
        need(u!=v,'graph has no self loops');pair=tuple(sorted(edge));need(pair not in seen,'graph has no repeated undirected edges');seen.add(pair)
        x,y=find(u),find(v)
        if tree: need(x!=y,'tree has no cycle')
        parents[x]=y
    if connected or tree: need(len({find(i) for i in range(n)})==1,'graph is connected')


def parent_tree(parents,root,name):
    n=len(parents);integer(parents[root],-1,-1,f'{name}[root]');children=[[] for _ in parents]
    for node,parent in enumerate(parents):
        if node==root: continue
        integer(parent,0,n-1,f'{name}[i]');need(parent!=node,'node is not its own parent');children[parent].append(node)
    reached={root};todo=[root]
    for node in todo:
        for child in children[node]:
            need(child not in reached,'parent relation has no cycle');reached.add(child);todo.append(child)
    need(len(reached)==n,'every node is reachable from the root')
    return children


def _tic_winner(moves):
    occupied=[set(),set()];winner=None
    wins=[{(r,c) for c in range(3)} for r in range(3)]+[{(r,c) for r in range(3)} for c in range(3)]+[{(i,i) for i in range(3)},{(i,2-i) for i in range(3)}]
    for i,move in enumerate(moves):
        need(winner is None,'no move may occur after tic-tac-toe game ends')
        occupied[i%2].add(tuple(move))
        if any(line<=occupied[i%2] for line in wins):winner='AB'[i%2]
    return winner or ('Draw' if len(moves)==9 else 'Pending')


def _time_options(value):
    return [f'{h:02}:{m:02}' for h in range(24) for m in range(60)
            if all(a=='?' or a==b for a,b in zip(value,f'{h:02}:{m:02}'))]


def _rectangles(land):
    rows,cols=len(land),len(land[0]);seen=set();result=[]
    for r in range(rows):
        for c in range(cols):
            if not land[r][c] or (r,c) in seen:continue
            component=[(r,c)];seen.add((r,c))
            for x,y in component:
                for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if 0<=nx<rows and 0<=ny<cols and land[nx][ny] and (nx,ny) not in seen:
                        seen.add((nx,ny));component.append((nx,ny))
            top=min(x for x,y in component);bottom=max(x for x,y in component)
            left=min(y for x,y in component);right=max(y for x,y in component)
            need(len(component)==(bottom-top+1)*(right-left+1),'each four-connected farmland group is a filled rectangle')
            result.append([top,left,bottom,right])
    return result


def _recover_pair_witness(values):
    ordered=sorted(values);counter=Counter(ordered)
    for delta in sorted({x-ordered[0] for x in ordered if x>ordered[0] and (x-ordered[0])%2==0}):
        counts=counter.copy();answer=[]
        for x in ordered:
            if counts[x]==0:continue
            if counts[x+delta]==0:break
            counts[x]-=1;counts[x+delta]-=1;answer.append(x+delta//2)
        else:return answer,delta//2
    return None


def _merge_noncoprime(values):
    result=[]
    for value in values:
        while result and gcd(value,result[-1])>1:value=lcm(value,result.pop())
        # No later merge can reduce an LCM, so early rejection is exact.
        need(value<=10**8,'values in final non-coprime merge array <= 100000000')
        result.append(value)
    return result


def validate(pid,args):
    need(pid in IDS,f'no independent expanded domain validator for {pid}')
    arity(args,{205:2,461:2,1310:2,1347:2,1376:4,1456:2,1462:3,1497:2,1583:3,
        1589:2,1604:2,1615:2,1616:2,1663:2,1700:2,1721:2,1738:2,1792:2,1803:3,
        1829:2,1870:2,1935:2,1946:2,1970:3,1986:2,2008:2,2024:2,2032:3,2040:3,
        2064:2,2068:2,2087:4,2099:2,2115:3,2162:4,2172:2,2215:2,2218:2,2220:2,
        2224:2,2250:2,2288:2,2303:2,2312:3,2334:2,2337:2,2343:2,2354:2,2368:3,
        2382:2,2402:2,2425:2,2429:2,2440:2,2458:2,2463:2,2470:2,2532:3,2561:2,
        2570:2,2586:3,2603:2,2646:4,2699:5,2851:3}.get(pid,1))
    a=args[0]
    if pid==171:
        text(a,1,7,UPPER,'columnTitle');need(len(a)<7 or a<='FXSHRXW','columnTitle is in [A, FXSHRXW]')
    elif pid in (190,191,231,258,263,405,1304,1432,1447,2376,2544,2578):
        bounds={190:(0,2**31-2),191:(1,2**31-1),231:(-2**31,2**31-1),258:(0,2**31-1),263:(-2**31,2**31-1),405:(-2**31,2**31-1),1304:(1,1000),1432:(1,10**8),1447:(1,100),2376:(1,2*10**9),2544:(1,10**9),2578:(10,10**9)}
        integer(a,*bounds[pid],'n')
        if pid==190:need(a%2==0,'n is even in pinned Reverse Bits statement')
    elif pid in (205,1347,1616,2068,2337):
        alphabet=''.join(map(chr,range(128))) if pid==205 else 'LR_' if pid==2337 else LOWER
        limit=100 if pid==2068 else 50000 if pid in (205,1347) else 100000
        text(a,1,limit,alphabet,'s');text(args[1],len(a),len(a),alphabet,'t')
    elif pid in (461,2220,2429):
        lower=1 if pid==2429 else 0;upper=2**31-1 if pid==461 else 10**9
        integer(a,lower,upper,'first');integer(args[1],lower,upper,'second')
    elif pid==448:numbers(a,1,100000,1,len(a) if isinstance(a,list) else 0,'nums')
    elif pid==1239:words(a,1,16,1,26,'arr')
    elif pid==1275:
        matrix(a,1,9,2,2,0,2,'moves');unique_rows(a,'moves');_tic_winner(a)
    elif pid==1282:
        numbers(a,1,500,1,len(a) if isinstance(a,list) else 0,'groupSizes')
        need(all(count%size==0 for size,count in Counter(a).items()),'each group-size frequency is divisible by that group size: solution exists')
    elif pid==1310:
        numbers(a,1,30000,1,10**9,'arr');array(args[1],1,30000,'queries')
        for query in args[1]:numbers(query,2,2,0,len(a)-1,'query');need(query[0]<=query[1],'query left <= right')
    elif pid==1376:
        n,head,manager,times=args;integer(n,1,100000,'n');integer(head,0,n-1,'headID');array(manager,n,n,'manager');numbers(times,n,n,0,1000,'informTime')
        children=parent_tree(manager,head,'manager');need(all(children[i] or times[i]==0 for i in range(n)),'employees without subordinates have informTime 0')
    elif pid==1451:
        parts=sentence(a,1,100000,LETTERS,'text');need(a[0] in UPPER and all(c in LOWER+' ' for c in a[1:]),'text starts with one uppercase letter then lowercase letters and spaces')
    elif pid==1456:text(a,1,100000,LOWER,'s');integer(args[1],1,len(a),'k')
    elif pid==1462:
        n,edges,queries=args;integer(n,2,100,'numCourses');array(edges,0,n*(n-1)//2,'prerequisites');unique_rows(edges,'prerequisites');adj=[[] for _ in range(n)];degrees=[0]*n
        for edge in edges:
            numbers(edge,2,2,0,n-1,'prerequisite');u,v=edge;need(u!=v,'no self prerequisite');adj[u].append(v);degrees[v]+=1
        queue=[i for i,d in enumerate(degrees) if d==0]
        for u in queue:
            for v in adj[u]:
                degrees[v]-=1
                if degrees[v]==0:queue.append(v)
        need(len(queue)==n,'prerequisite graph has no cycles');array(queries,1,10000,'queries')
        for query in queries:numbers(query,2,2,0,n-1,'query');need(query[0]!=query[1],'query endpoints differ')
    elif pid==1491:numbers(a,3,100,1000,10**6,'salary',True)
    elif pid==1497:
        numbers(a,1,100000,-10**9,10**9,'arr');need(len(a)%2==0,'arr length is even');integer(args[1],1,100000,'k')
    elif pid==1583:
        n,prefs,pairs=args;integer(n,2,500,'n');need(n%2==0,'n is even');array(prefs,n,n,'preferences')
        for i,row in enumerate(prefs):numbers(row,n-1,n-1,0,n-1,'preferences[i]',True);need(i not in row,'preferences exclude self')
        array(pairs,n//2,n//2,'pairs');seen=[]
        for pair in pairs:numbers(pair,2,2,0,n-1,'pair',True);seen+=pair
        need(len(set(seen))==n,'each person is in exactly one pair')
    elif pid==1589:
        numbers(a,1,100000,0,100000,'nums');array(args[1],1,100000,'requests')
        for request in args[1]:numbers(request,2,2,0,len(a)-1,'request');need(request[0]<=request[1],'request start <= end')
    elif pid==1604:
        words(a,1,100000,1,10,'keyName');array(args[1],len(a),len(a),'keyTime')
        for time in args[1]:clock(time)
        need(len(set(zip(a,args[1])))==len(a),'[keyName,keyTime] pairs are unique')
    elif pid==1615:integer(a,2,100,'n');simple_graph(a,args[1])
    elif pid==1619:numbers(a,20,1000,0,100000,'arr');need(len(a)%20==0,'arr.length is a multiple of 20')
    elif pid==1663:integer(a,1,100000,'n');integer(args[1],a,26*a,'k')
    elif pid==1700:numbers(a,1,100,0,1,'students');numbers(args[1],len(a),len(a),0,1,'sandwiches')
    elif pid==1704:text(a,2,1000,LETTERS,'s');need(len(a)%2==0,'s.length is even')
    elif pid==1721:
        values=common.list_values(a,1,100000,0,100);integer(args[1],1,len(values),'k')
    elif pid==1736:
        text(a,5,5,string.digits+'?:','time');need(a[2]==':' and ':' not in a[:2]+a[3:],'time is hh:mm');need(bool(_time_options(a)),'at least one valid 24-hour time matches input')
    elif pid==1738:
        h,w=matrix(a,1,1000,1,1000,0,10**6,'matrix');integer(args[1],1,h*w,'k')
    elif pid==1776:
        matrix(a,1,100000,2,2,1,10**6,'cars');need(all(x[0]<y[0] for x,y in zip(a,a[1:])),'car positions strictly increase')
    elif pid==1792:
        matrix(a,1,100000,2,2,1,100000,'classes');need(all(p<=t for p,t in a),'pass <= total');integer(args[1],1,100000,'extraStudents')
    elif pid==1803:
        numbers(a,1,20000,1,20000,'nums');integer(args[1],1,20000,'low');integer(args[2],args[1],20000,'high')
    elif pid==1829:
        integer(args[1],1,20,'maximumBit');numbers(a,1,100000,0,2**args[1]-1,'nums');need(a==sorted(a),'nums is sorted ascending')
    elif pid==1870:numbers(a,1,100000,1,100000,'dist');numeric(args[1],1,10**9,'hour',2)
    elif pid==1916:array(a,2,100000,'prevRoom');parent_tree(a,0,'prevRoom')
    elif pid==1935:
        sentence(a,1,10000,LOWER,'text');text(args[1],0,26,LOWER,'brokenLetters');need(len(set(args[1]))==len(args[1]),'brokenLetters are distinct')
    elif pid==1946:text(a,1,100000,string.digits,'num');numbers(args[1],10,10,0,9,'change')
    elif pid==1963:text(a,2,10**6,'[]','s');need(a.count('[')==a.count(']'),'equal numbers of opening and closing brackets')
    elif pid==1968:numbers(a,3,100000,0,100000,'nums',True)
    elif pid==1970:
        row,col,cells=args;integer(row,2,20000,'row');integer(col,2,20000,'col');need(row*col<=20000,'row*col <= 20000');array(cells,row*col,row*col,'cells')
        for cell in cells:array(cell,2,2,'cell');integer(cell[0],1,row,'cell row');integer(cell[1],1,col,'cell col')
        unique_rows(cells,'cells')
    elif pid==1980:
        array(a,1,16,'nums');words(a,len(a),len(a),len(a),len(a),'nums','01',True)
    elif pid==1986:numbers(a,1,14,1,10,'tasks');integer(args[1],max(a),15,'sessionTime')
    elif pid==1992:matrix(a,1,300,1,300,0,1,'land');_rectangles(a)
    elif pid==1994:numbers(a,1,100000,1,30,'nums')
    elif pid==2008:
        integer(a,1,100000,'n');array(args[1],1,30000,'rides')
        for ride in args[1]:array(ride,3,3,'ride');integer(ride[0],1,a,'start');integer(ride[1],ride[0]+1,a,'end');integer(ride[2],1,100000,'tip')
    elif pid==2024:text(a,1,50000,'TF','answerKey');integer(args[1],1,len(a),'k')
    elif pid==2032:
        for i,values in enumerate(args):numbers(values,1,100,1,100,f'nums{i+1}')
    elif pid==2040:
        for i,values in enumerate(args[:2]):numbers(values,1,50000,-100000,100000,f'nums{i+1}');need(values==sorted(values),'arrays sorted ascending')
        integer(args[2],1,len(a)*len(args[1]),'k')
    elif pid==2042:
        tokens=sentence(a,3,200,LOWER+string.digits,'s');need(2<=len(tokens)<=100,'s has 2..100 tokens');count=0
        for token in tokens:
            if token.isascii() and token.isdigit():
                need(re.fullmatch('[1-9][0-9]?',token) is not None,'numeric tokens positive <100 with no leading zeros');count+=1
            else:need(set(token)<=set(LOWER),'tokens are lowercase words or numbers')
        need(count>=2,'s contains at least two numbers')
    elif pid==2064:integer(a,1,100000,'n');numbers(args[1],1,a,1,100000,'quantities')
    elif pid==2087:
        start,home,rows,cols=args;numbers(rows,1,100000,0,10000,'rowCosts');numbers(cols,1,100000,0,10000,'colCosts')
        for name,point in [('startPos',start),('homePos',home)]:array(point,2,2,name);integer(point[0],0,len(rows)-1,name+' row');integer(point[1],0,len(cols)-1,name+' col')
    elif pid==2097:
        matrix(a,1,100000,2,2,0,10**9,'pairs');unique_rows(a,'pairs');degree=Counter();neighbors=defaultdict(list)
        for u,v in a:need(u!=v,'pair endpoints differ');degree[u]+=1;degree[v]-=1;neighbors[u].append(v);neighbors[v].append(u)
        deltas=list(degree.values());need(all(abs(x)<=1 for x in deltas) and deltas.count(1)==deltas.count(-1)<=1,'directed degrees admit an Euler trail')
        seen={a[0][0]};todo=list(seen)
        for u in todo:
            for v in neighbors[u]:
                if v not in seen:seen.add(v);todo.append(v)
        need(len(seen)==len(neighbors),'all directed pairs lie in one weakly connected component')
    elif pid==2099:numbers(a,1,1000,-100000,100000,'nums');integer(args[1],1,len(a),'k')
    elif pid==2115:
        recipes,ingredients,supplies=args;words(recipes,1,100,1,10,'recipes',distinct=True);array(ingredients,len(recipes),len(recipes),'ingredients');words(supplies,1,100,1,10,'supplies',distinct=True)
        need(len(set(recipes+supplies))==len(recipes)+len(supplies),'recipes and supplies combined are unique')
        for row in ingredients:words(row,1,100,1,10,'ingredients[i]',distinct=True)
    elif pid==2122:
        numbers(a,2,2000,1,10**9,'nums');need(len(a)%2==0,'nums length equals 2*n');need(_recover_pair_witness(a) is not None,'input has a positive-array, positive-integer-offset recovery')
    elif pid==2133:
        h,w=matrix(a,1,100,1,100,1,100,'matrix');need(h==w,'matrix square');need(all(v<=h for row in a for v in row),'matrix entries <= n')
    elif pid==2162:
        integer(a,0,9,'startAt');integer(args[1],1,100000,'moveCost');integer(args[2],1,100000,'pushCost');integer(args[3],1,6039,'targetSeconds')
    elif pid==2163:numbers(a,3,300000,1,100000,'nums');need(len(a)%3==0,'nums.length == 3*n')
    elif pid==2172:integer(args[1],1,9,'numSlots');numbers(a,1,2*args[1],1,15,'nums')
    elif pid==2193:text(a,1,2000,LOWER,'s');need(sum(count%2 for count in Counter(a).values())<=1,'s has a palindrome permutation')
    elif pid==2194:
        text(a,5,5,UPPER+'123456789:','s');need(re.fullmatch('[A-Z][1-9]:[A-Z][1-9]',a) is not None,'range format is column-row:column-row');need(a[0]<=a[3] and a[1]<=a[4],'range endpoints nondecreasing in column and row')
    elif pid==2197:numbers(a,1,100000,1,100000,'nums');_merge_noncoprime(a)
    elif pid==2215:
        for values in args:numbers(values,1,1000,-1000,1000,'nums')
    elif pid==2218:
        array(a,1,1000,'piles');total=0
        for pile in a:numbers(pile,1,2000,1,100000,'pile');total+=len(pile)
        need(total<=2000,'total number of coins <= 2000');integer(args[1],1,total,'k')
    elif pid==2224:need(clock(a,'current')<=clock(args[1],'correct'),'current <= correct')
    elif pid==2249:
        array(a,1,200,'circles')
        for circle in a:array(circle,3,3,'circle');integer(circle[0],1,100,'x');integer(circle[1],1,100,'y');integer(circle[2],1,min(circle[:2]),'radius')
    elif pid==2250:
        for name,values in zip(('rectangles','points'),args):
            array(values,1,50000,name)
            for pair in values:array(pair,2,2,name+'[i]');integer(pair[0],1,10**9,'x/length');integer(pair[1],1,100,'y/height')
            unique_rows(values,name)
    elif pid==2273:words(a,1,100,1,10,'words')
    elif pid==2288:
        tokens=sentence(a,1,100000,LOWER+string.digits+'$','sentence');integer(args[1],0,100,'discount')
        for token in tokens:
            if re.fullmatch(r'\$[0-9]+',token):need(re.fullmatch(r'\$[1-9][0-9]{0,9}',token) is not None,'prices positive, no leading zeros, <=10 digits')
    elif pid==2293:numbers(a,1,1024,1,10**9,'nums');need(len(a)&(len(a)-1)==0,'nums length is a power of two')
    elif pid==2303:
        array(a,1,100,'brackets');previous=0
        for row in a:array(row,2,2,'bracket');integer(row[0],previous+1,1000,'upper');integer(row[1],0,100,'percent');previous=row[0]
        integer(args[1],0,1000,'income');need(previous>=args[1],'last bracket upper >= income')
    elif pid==2306:words(a,2,50000,1,10,'ideas',distinct=True)
    elif pid==2312:
        m,n,prices=args;integer(m,1,200,'m');integer(n,1,200,'n');array(prices,1,20000,'prices');seen=set()
        for row in prices:array(row,3,3,'price');h,w,p=row;integer(h,1,m,'height');integer(w,1,n,'width');integer(p,1,10**6,'price');need((h,w) not in seen,'wood shapes are distinct');seen.add((h,w))
    elif pid==2317:numbers(a,1,100000,0,10**8,'nums')
    elif pid==2331:
        nodes=common.tree_nodes(a,1,1000,0,3)
        for value,left,right in nodes:
            need((left is None)==(right is None),'each node has zero or two children');need(value in ((0,1) if left is None else (2,3)),'leaf values 0/1 and internal operators 2/3')
    elif pid==2334:numbers(a,1,100000,1,10**9,'nums');integer(args[1],1,10**9,'threshold')
    elif pid==2343:
        words(a,1,100,1,100,'nums',string.digits);need(len({len(s) for s in a})==1,'all numeric strings have equal length');array(args[1],1,100,'queries')
        for q in args[1]:array(q,2,2,'query');integer(q[0],1,len(a),'k');integer(q[1],1,len(a[0]),'trim')
    elif pid==2354:numbers(a,1,100000,1,10**9,'nums');integer(args[1],1,60,'k')
    elif pid==2368:
        n,edges,restricted=args;integer(n,2,100000,'n');simple_graph(n,edges,tree=True);numbers(restricted,1,n-1,1,n-1,'restricted',True)
    elif pid==2382:numbers(a,1,100000,1,10**9,'nums');numbers(args[1],len(a),len(a),0,len(a)-1,'removeQueries',True)
    elif pid==2402:
        integer(a,1,100,'n');array(args[1],1,100000,'meetings');starts=set()
        for row in args[1]:array(row,2,2,'meeting');integer(row[0],0,499999,'start');integer(row[1],row[0]+1,500000,'end');need(row[0] not in starts,'meeting starts unique');starts.add(row[0])
    elif pid==2425:
        for values in args:numbers(values,1,100000,0,10**9,'nums')
    elif pid==2440:numbers(a,1,20000,1,50,'nums');simple_graph(len(a),args[1],tree=True)
    elif pid==2458:
        nodes=common.tree_nodes(a,2,100000,1,100000);values=[row[0] for row in nodes];need(set(values)==set(range(1,len(nodes)+1)),'tree values are unique 1..n');numbers(args[1],1,min(len(nodes),10000),1,len(nodes),'queries');need(nodes[0][0] not in args[1],'queries exclude tree root')
    elif pid==2463:
        numbers(a,1,100,-10**9,10**9,'robot',True);array(args[1],1,100,'factory');positions=[];capacity=0
        for row in args[1]:array(row,2,2,'factory[i]');integer(row[0],-10**9,10**9,'factory position');integer(row[1],0,len(a),'factory limit');positions.append(row[0]);capacity+=row[1]
        need(len(set(positions))==len(positions),'factory positions unique');need(capacity>=len(a),'total factory capacity permits repairing every robot')
    elif pid==2465:numbers(a,2,100,0,100,'nums');need(len(a)%2==0,'nums length even')
    elif pid==2469:numeric(a,0,1000,'celsius',2)
    elif pid==2470:numbers(a,1,1000,1,1000,'nums');integer(args[1],1,1000,'k')
    elif pid==2532:
        n,k,times=args;integer(n,1,10000,'n');integer(k,1,10000,'k');matrix(times,k,k,4,4,1,1000,'time')
    elif pid==2553:numbers(a,1,1000,1,100000,'nums')
    elif pid==2561:numbers(a,1,100000,1,10**9,'basket1');numbers(args[1],len(a),len(a),1,10**9,'basket2')
    elif pid==2570:
        for rows in args:
            matrix(rows,1,200,2,2,1,1000,'nums');need(all(x[0]<y[0] for x,y in zip(rows,rows[1:])),'array ids strictly increase')
    elif pid==2584:numbers(a,1,10000,1,10**6,'nums')
    elif pid==2586:words(a,1,1000,1,10,'words');integer(args[1],0,len(a)-1,'left');integer(args[2],args[1],len(a)-1,'right')
    elif pid==2589:
        array(a,1,2000,'tasks')
        for row in a:array(row,3,3,'task');integer(row[0],1,2000,'start');integer(row[1],row[0],2000,'end');integer(row[2],1,row[1]-row[0]+1,'duration')
    elif pid==2603:numbers(a,1,30000,0,1,'coins');simple_graph(len(a),args[1],tree=True)
    elif pid==2646:
        n,edges,price,trips=args;integer(n,1,50,'n');simple_graph(n,edges,tree=True);numbers(price,n,n,1,1000,'price');need(all(p%2==0 for p in price),'prices are even');matrix(trips,1,100,2,2,0,n-1,'trips')
    elif pid==2699:
        n,edges,source,dest,target=args;integer(n,1,100,'n');array(edges,1,n*(n-1)//2,'edges');pairs=[]
        for row in edges:array(row,3,3,'edge');u,v,w=row;numbers([u,v],2,2,0,n-1,'endpoints');need(type(w) is int and (w==-1 or 1<=w<=10**7),'weight is -1 or integer in [1,10000000]');pairs.append([u,v])
        simple_graph(n,pairs,connected=True);integer(source,0,n-1,'source');integer(dest,0,n-1,'destination');need(source!=dest,'source != destination');integer(target,1,10**9,'target')
    elif pid==2732:matrix(a,1,10000,1,5,0,1,'grid')
    elif pid==2851:text(a,2,500000,LOWER,'s');text(args[1],len(a),len(a),LOWER,'t');integer(args[2],1,10**15,'k')
    else:raise DomainError(f'expanded validator missing {pid}')


def expected(pid,args):
    """Independent definition-level answers; deliberately no source imports."""
    validate(pid,args)
    if pid not in ORACLE_IDS:raise ValueError(f'no expanded independent oracle for {pid}')
    a=args[0]
    if pid==171:
        result=0
        for c in a:result=result*26+ord(c)-64
        return result
    if pid==190:return int(format(a,'032b')[::-1],2)
    if pid==191:return bin(a).count('1')
    if pid==205:return len(set(a))==len(set(args[1]))==len(set(zip(a,args[1])))
    if pid==231:return a>0 and a&(a-1)==0
    if pid==258:
        while a>=10:a=sum(map(int,str(a)))
        return a
    if pid==263:
        if a<=0:return False
        for prime in (2,3,5):
            while a%prime==0:a//=prime
        return a==1
    if pid==405:return format(a%(2**32),'x')
    if pid==448:return sorted(set(range(1,len(a)+1))-set(a))
    if pid in (461,2220):return bin(a^args[1]).count('1')
    if pid==1275:return _tic_winner(a)
    if pid==1310:
        prefix=[0]
        for x in a:prefix.append(prefix[-1]^x)
        return [prefix[r+1]^prefix[l] for l,r in args[1]]
    if pid==1347:return sum((Counter(a)-Counter(args[1])).values())
    if pid==1432:
        values=[]
        for old in string.digits:
            for new in string.digits:
                changed=str(a).replace(old,new)
                if changed[0]!='0':values.append(int(changed))
        return max(values)-min(values)
    if pid==1447:return [f'{p}/{q}' for q in range(2,a+1) for p in range(1,q) if gcd(p,q)==1]
    if pid==1451:
        result=' '.join(sorted(a.lower().split(' '),key=len));return result[0].upper()+result[1:]
    if pid==1456:
        k=args[1];prefix=[0]
        for c in a:prefix.append(prefix[-1]+(c in 'aeiou'))
        return max(prefix[i+k]-prefix[i] for i in range(len(a)-k+1))
    if pid==1491:return float(Fraction(sum(a)-max(a)-min(a),len(a)-2))
    if pid==1497:
        counts=Counter(x%args[1] for x in a);k=args[1]
        return all(count%2==0 if (2*r)%k==0 else count==counts[k-r] for r,count in counts.items())
    if pid==1583:
        n,prefs,pairs=args;partner={}
        for x,y in pairs:partner[x]=y;partner[y]=x
        rank=[{v:i for i,v in enumerate(row)} for row in prefs]
        return sum(any(rank[x][u]<rank[x][partner[x]] and rank[u][x]<rank[u][partner[u]] for u in prefs[x]) for x in range(n))
    if pid==1604:
        times=defaultdict(list)
        for name,time in zip(a,args[1]):times[name].append(clock(time))
        return sorted(name for name,visits in times.items() if any(y-x<=60 for x,y in zip(sorted(visits),sorted(visits)[2:])))
    if pid==1615:
        adj=[set() for _ in range(a)]
        for u,v in args[1]:adj[u].add(v);adj[v].add(u)
        return max(len(adj[u])+len(adj[v])-(v in adj[u]) for u in range(a) for v in range(u+1,a))
    if pid==1616:
        def joinable(first,second):
            left,right=0,len(first)-1
            while left<right and first[left]==second[right]:left+=1;right-=1
            return any(s[left:right+1]==s[left:right+1][::-1] for s in (first,second))
        return joinable(*args) or joinable(*reversed(args))
    if pid==1619:
        trimmed=sorted(a)[len(a)//20:-len(a)//20];return float(Fraction(sum(trimmed),len(trimmed)))
    if pid==1663:
        remaining=args[1];letters=[]
        for position in range(a):
            smallest=max(1,remaining-26*(a-position-1));letters.append(chr(96+smallest));remaining-=smallest
        return ''.join(letters)
    if pid==1700:
        counts=Counter(a)
        for sandwich in args[1]:
            if not counts[sandwich]:break
            counts[sandwich]-=1
        return sum(counts.values())
    if pid==1704:return sum(c.lower() in 'aeiou' for c in a[:len(a)//2])==sum(c.lower() in 'aeiou' for c in a[len(a)//2:])
    if pid==1736:return max(_time_options(a))
    if pid==1738:
        columns=[0]*len(a[0]);values=[]
        for row in a:
            prefix=0
            for c,v in enumerate(row):columns[c]^=v;prefix^=columns[c];values.append(prefix)
        return sorted(values,reverse=True)[args[1]-1]
    if pid==1829:
        total=0
        for x in a:total^=x
        mask=2**args[1]-1;result=[]
        for x in reversed(a):result.append(total^mask);total^=x
        return result
    if pid==1935:return sum(not(set(word)&set(args[1])) for word in a.split(' '))
    if pid==1946:
        result=list(a);begun=False
        for i,c in enumerate(a):
            replacement=str(args[1][int(c)])
            if replacement>c:begun=True
            if begun and replacement<c:break
            if begun:result[i]=replacement
        return ''.join(result)
    if pid==1963:
        balance=minimum=0
        for c in a:balance+=1 if c=='[' else -1;minimum=min(minimum,balance)
        return (-minimum+1)//2
    if pid==1992:return _rectangles(a)
    if pid==1994:
        counts=Counter(a);primes=(2,3,5,7,11,13,17,19,23,29);ways={0:1}
        for value,count in sorted(counts.items()):
            if value==1 or any(value%(p*p)==0 for p in primes):continue
            mask=sum(1<<i for i,p in enumerate(primes) if value%p==0)
            additions=defaultdict(int)
            for used,total in ways.items():
                if used&mask==0:additions[used|mask]=(additions[used|mask]+total*count)%MOD
            for used,total in additions.items():ways[used]=(ways.get(used,0)+total)%MOD
        return sum(v for mask,v in ways.items() if mask)*pow(2,counts[1],MOD)%MOD
    if pid==2024:
        best=0
        for chosen in 'TF':
            left=changed=0
            for right,c in enumerate(a):
                changed+=c!=chosen
                while changed>args[1]:changed-=a[left]!=chosen;left+=1
                best=max(best,right-left+1)
        return best
    if pid==2032:
        counts=Counter(v for values in args for v in set(values));return sorted(v for v,c in counts.items() if c>=2)
    if pid==2042:
        nums=[int(token) for token in a.split() if token.isdigit()];return all(x<y for x,y in zip(nums,nums[1:]))
    if pid==2064:
        left,right=1,max(args[1])
        while left<right:
            middle=(left+right)//2
            if sum((v+middle-1)//middle for v in args[1])<=a:right=middle
            else:left=middle+1
        return left
    if pid==2068:
        first,second=map(Counter,args);return all(abs(first[c]-second[c])<=3 for c in LOWER)
    if pid==2087:
        start,home,rows,cols=args;total=0
        for first,last,costs in ((start[0],home[0],rows),(start[1],home[1],cols)):
            if first<last:total+=sum(costs[first+1:last+1])
            elif first>last:total+=sum(costs[last:first])
        return total
    if pid==2115:
        recipes,ingredients,supplies=args;available=set(supplies)
        while True:
            added={recipe for recipe,items in zip(recipes,ingredients) if set(items)<=available}-available
            if not added:break
            available|=added
        return sorted(set(recipes)&available)
    if pid==2133:
        wanted=set(range(1,len(a)+1));return all(set(row)==wanted for row in a) and all(set(col)==wanted for col in zip(*a))
    if pid==2162:
        start,move,push,target=args;costs=[]
        for minute in range(100):
            second=target-60*minute
            if not 0<=second<=99:continue
            digits=f'{minute:02}{second:02}'.lstrip('0');finger=str(start);cost=0
            for digit in digits:cost+=push+(move if digit!=finger else 0);finger=digit
            costs.append(cost)
        return min(costs)
    if pid==2194:return [c+r for c in UPPER[ord(a[0])-65:ord(a[3])-64] for r in string.digits[int(a[1]):int(a[4])+1]]
    if pid==2197:return _merge_noncoprime(a)
    if pid==2215:return [sorted(set(a)-set(args[1])),sorted(set(args[1])-set(a))]
    if pid==2224:
        remaining=clock(args[1])-clock(a);count=0
        for step in (60,15,5,1):part,remaining=divmod(remaining,step);count+=part
        return count
    if pid==2249:
        from math import isqrt
        columns=defaultdict(list)
        for cx,cy,r in a:
            for x in range(cx-r,cx+r+1):
                dy=isqrt(r*r-(x-cx)**2);columns[x].append((cy-dy,cy+dy))
        count=0
        for intervals in columns.values():
            low=high=None
            for left,right in sorted(intervals):
                if low is None:low,high=left,right
                elif left>high+1:count+=high-low+1;low,high=left,right
                else:high=max(high,right)
            count+=high-low+1
        return count
    if pid==2273:
        result=[];previous=None
        for word in a:
            signature=tuple(sorted(Counter(word).items()))
            if signature!=previous:result.append(word);previous=signature
        return result
    if pid==2288:
        result=[]
        for token in a.split(' '):
            if re.fullmatch(r'\$[0-9]+',token):
                cents=int(token[1:])*(100-args[1]);token=f'${cents//100}.{cents%100:02}'
            result.append(token)
        return ' '.join(result)
    if pid==2293:
        values=a[:]
        while len(values)>1:values=[(min if i%2==0 else max)(values[2*i:2*i+2]) for i in range(len(values)//2)]
        return values[0]
    if pid==2303:
        previous=hundredths=0
        for upper,percent in a:
            taxed=max(0,min(args[1],upper)-previous);hundredths+=taxed*percent;previous=upper
        return float(Fraction(hundredths,100))
    if pid==2306:
        groups=defaultdict(set)
        for idea in a:groups[idea[0]].add(idea[1:])
        return sum(2*len(x-y)*len(y-x) for x,y in combinations(groups.values(),2))
    if pid==2317:
        # Operation only clears selected set bits. Retain each present bit in
        # exactly one element to attain their union as the final XOR.
        result=0
        for value in a:result|=value
        return result
    if pid==2331:
        nodes=common.tree_nodes(a,1,1000,0,3);values=[False]*len(nodes)
        for i in range(len(nodes)-1,-1,-1):
            value,left,right=nodes[i]
            values[i]=bool(value) if left is None else (values[left] or values[right]) if value==2 else (values[left] and values[right])
        return values[0]
    if pid==2337:
        first=[(i,c) for i,c in enumerate(a) if c!='_'];second=[(i,c) for i,c in enumerate(args[1]) if c!='_']
        return len(first)==len(second) and all(c==d and (i>=j if c=='L' else i<=j) for (i,c),(j,d) in zip(first,second))
    if pid==2343:return [sorted(range(len(a)),key=lambda i:(a[i][-trim:],i))[k-1] for k,trim in args[1]]
    if pid==2354:
        counts=Counter(bin(v).count('1') for v in set(a));return sum(c*d for x,c in counts.items() for y,d in counts.items() if x+y>=args[1])
    if pid==2425:
        result=0
        if len(args[1])%2:
            for v in a:result^=v
        if len(a)%2:
            for v in args[1]:result^=v
        return result
    if pid==2429:
        # Lexicographically minimize XOR bits from most significant downward.
        quota=bin(args[1]).count('1');result=0
        for bit in range(30,-1,-1):
            if quota and a&(1<<bit):result|=1<<bit;quota-=1
        for bit in range(31):
            if quota and result&(1<<bit)==0:result|=1<<bit;quota-=1
        return result
    if pid==2465:
        values=sorted(a);return len({values[i]+values[-i-1] for i in range(len(a)//2)})
    if pid==2469:
        value=Fraction(str(a));return [float(value+Fraction(27315,100)),float(value*Fraction(9,5)+32)]
    if pid==2470:
        answer=0;k=args[1]
        for start in range(len(a)):
            current=1
            for end in range(start,len(a)):
                current=lcm(current,a[end])
                if k%current:break
                answer+=current==k
        return answer
    if pid==2544:return sum(int(c)*(1 if i%2==0 else -1) for i,c in enumerate(str(a)))
    if pid==2553:return [int(c) for value in a for c in str(value)]
    if pid==2570:
        sums=Counter()
        for rows in args:
            for key,value in rows:sums[key]+=value
        return [[key,value] for key,value in sorted(sums.items())]
    if pid==2578:
        # Largest decimal places belong to smallest digits, with balanced
        # digit counts across the two numbers; alternating sorted digits does so.
        digits=sorted(str(a));return int(''.join(digits[::2]) or '0')+int(''.join(digits[1::2]) or '0')
    if pid==2586:return sum(word[0] in 'aeiou' and word[-1] in 'aeiou' for word in a[args[1]:args[2]+1])
    raise AssertionError(f'expanded oracle missing {pid}')


def agrees(pid,got,want):
    if pid in (1491,1619,2303):return type(want) in (int,float) and isfinite(want) and abs(got-want)<=1e-5
    if pid==2469:return type(want) is list and len(want)==2 and all(type(y) in (int,float) and isfinite(y) and abs(x-y)<=1e-5 for x,y in zip(got,want))
    if pid in (1447,1992,2032,2115):
        try:return type(want) is list and common.exact(sorted(got),sorted(want))
        except TypeError:return False
    if pid==2215:
        try:return type(want) is list and len(want)==2 and all(type(y) is list and common.exact(sorted(x),sorted(y)) for x,y in zip(got,want))
        except TypeError:return False
    return common.exact(got,want)


def admit_case(pid,case):
    original=deepcopy(case)
    try:
        need(type(case) is dict and set(case)=={'args','expected','compare'},'case fields are args,expected,compare')
        need(case['compare']=='return','comparison is return');validate(pid,case['args'])
    except DomainError as error:return {'status':'rejected-domain','reason':str(error),'original':original}
    if pid not in ORACLE_IDS:return {'status':'domain-valid-oracle-unreviewed','original':original}
    wanted=expected(pid,case['args']);corrected=deepcopy(case);corrected['expected']=wanted
    return {'status':'oracle-confirmed' if agrees(pid,wanted,case['expected']) else 'oracle-corrected',
        'original':original,'case':corrected,'comparison_policy':COMPARISON_POLICIES.get(pid,'exact'),
        'reason':'independent statement-level oracle; no candidate source or observation consulted'}


def public_examples(pid,raw):
    clean=re.sub(r'</?(?:p|pre|div|li|ul|ol|br)\b[^>]*>','\n',raw.decode())
    clean=html.unescape(re.sub('<[^>]*>','',clean)).replace('\xa0',' ')
    class Names(ast.NodeTransformer):
        def visit_Name(self,node):
            if node.id not in ('true','false','null'):raise ValueError('unexpected bare example token')
            return ast.copy_location(ast.Constant({'true':True,'false':False,'null':None}[node.id]),node)
    reviewed=[]
    for match in re.finditer(r'Input:\s*(.*?)\s*Output:\s*(.*?)(?=Explanation:|Explantion:|Explaination:|Example\s*\d+:|Constraints:|$)',clean,re.S):
        call=ast.parse('f('+match[1].strip()+')',mode='eval').body
        if not isinstance(call,ast.Call) or call.args or not call.keywords or any(k.arg is None for k in call.keywords):raise ValueError('unsupported public example argument syntax')
        args=[ast.literal_eval(Names().visit(k.value)) for k in call.keywords]
        if pid in (2331,2458):args[0]={'__tree_node__':args[0]}
        if pid==1721:args[0]={'__list_node__':args[0]}
        validate(pid,args)
        row={'args':args,'domain_checked':True}
        if pid in ORACLE_IDS:
            want=ast.literal_eval(Names().visit(ast.parse(match[2].strip(),mode='eval')).body)
            got=expected(pid,args)
            if not agrees(pid,got,want):raise ValueError(f'expanded oracle/public example mismatch {pid}: {got!r} != {want!r}')
            row.update(expected=got,public_expected=want,oracle_checked=True)
        reviewed.append(row)
    if not reviewed:raise ValueError(f'no public examples for {pid}')
    return reviewed


def sha(raw):return hashlib.sha256(raw).hexdigest()


def audit(freeze,gate_path,output):
    from .boundary_policy import authorize_before_open
    freeze=Path(freeze);contract_raw=(freeze/'contract.json').read_bytes()
    need(sha(contract_raw)=='38aa4b0b1e6e205c47342da786c9dc25ff9f6c10a77511ae831ed0a99c3bcdd5',
         'audit requires the exact expanded diagnostic freeze-v1 contract')
    contract=json.loads(contract_raw)
    gate=json.loads(Path(gate_path).read_text());jobs={j['id']:j for j in contract['jobs'] if j['id'] in IDS}
    need(set(jobs)==IDS,'expanded freeze contains all 114 selected IDs')
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    report={'schema':'gamma.expanded-case-admission.v1','freeze_contract_sha256':sha(contract_raw),
        'module_sha256':sha(Path(__file__).read_bytes()),'helper_module_sha256':sha(Path(common.__file__).read_bytes()),
        'candidate_sources_opened':False,'candidate_observations_opened':False,'candidate_executions':0,
        'diagnostic_failure_categories_consulted':True,
        'automatic_promotion':False,'new_qualifications':0,'problems':[]}
    for pid,job in sorted(jobs.items()):
        authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language='python',payload_kind='statement')
        raw=Path(job['statement']['path']).read_bytes();need(sha(raw)==job['statement']['sha256'],'pinned statement hash matches')
        examples=public_examples(pid,raw)
        authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language='python')
        path=freeze/job['tests'];need(path.stat().st_size<=8*1024**2,'case file <=8 MiB');raw=path.read_bytes();need(sha(raw)==job['tests_raw_sha256'],'pinned historical tests hash matches')
        cases=json.loads(raw);decisions=[dict(index=i,**admit_case(pid,case)) for i,case in enumerate(cases)]
        payload={'id':pid,'statement':job['statement'],'original_tests_sha256':sha(raw),'public_examples':examples,
                 'comparison_policy':COMPARISON_POLICIES.get(pid,'exact'),'decisions':decisions}
        encoded=json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n';(output/f'{pid}.json').write_bytes(encoded)
        report['problems'].append({'id':pid,'case_count':len(cases),'public_examples':len(examples),'public_oracle_examples':sum(x.get('oracle_checked',False) for x in examples),
            'counts':dict(Counter(d['status'] for d in decisions)),
            'rejection_reasons':dict(Counter(d['reason'] for d in decisions if d['status']=='rejected-domain')),
            'artifact':f'{pid}.json','sha256':sha(encoded)})
    report['counts']=dict(sum((Counter(r['counts']) for r in report['problems']),Counter()))
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze',required=True);parser.add_argument('--gate',dest='gate_path',required=True);parser.add_argument('--output',required=True)
    result=audit(**vars(parser.parse_args()));print(json.dumps({'problems':len(result['problems']),'counts':result['counts']}))
