"""Statement-domain admission for historical independent cases, never candidates.

These validators are derived from the pinned statement snapshots at doocs
88c8c2c29f19c186d7cc05c9db17245d9ae3df43. Unsupported IDs fail closed.
Domain validity is not oracle validity. Only ORACLE_IDS have independently
recomputed expected answers here; other admitted cases still need an oracle
review. Original cases are never overwritten. The audit command binds statements,
input cases and this module by SHA-256, retaining every rejection and correction.
No source execution, qualification receipt creation or catalogue promotion occurs.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import html
import json
from math import comb
from pathlib import Path
import re
import string

LOWER = string.ascii_lowercase
UPPER = string.ascii_uppercase
LETTERS = LOWER + UPPER
DOMAIN_IDS = frozenset((68,660,1256,1283,1289,1324,1337,1356,1365,1366,1383,1395,
    1439,1444,1554,1560,1569,1575,1601,1606,1610,1639,1643,1678,1681,1687,
    1701,1703,1711,1734,1755,1775,1859,1915,1941,1954,1966,2007,2059,2109,
    2231,2268,2305,2311,2387,2391,2399,2401,2403,2411,2450,2457,2562,2639,
    2659,2680,2710,2733,2744,2802,2817,2847,2855,2869,2933,2937,2965,3004,
    3013,3074,3079,3114,3120,3132,3158,3159,3167,3194,3218))
ORACLE_IDS = frozenset((68,660,1324,1337,1356,1365,1366,1395,1560,1569,1643,
    1678,1701,1734,1859,1941,2109,2231,2268,2399,2450,2562,2639,2710,2744,
    2802,2855,2869,2933,2937,2965,3074,3079,3114,3120,3132,3158,3159,3167,3194,3218))


class DomainError(ValueError):
    """The exact statement constraint not satisfied by a historical input."""


def need(condition, constraint):
    if not condition:
        raise DomainError(constraint)


def integer(value, lo, hi, name):
    need(type(value) is int and lo <= value <= hi, f'{name} must be an integer in [{lo}, {hi}]')


def array(value, lo, hi, name):
    need(type(value) is list and lo <= len(value) <= hi, f'{name}.length must be in [{lo}, {hi}]')


def numbers(value, nlo, nhi, vlo, vhi, name, distinct=False):
    array(value, nlo, nhi, name)
    for x in value:
        integer(x, vlo, vhi, f'{name}[i]')
    if distinct:
        need(len(set(value)) == len(value), f'{name} values must be distinct')


def text(value, lo, hi, alphabet, name):
    need(type(value) is str and lo <= len(value) <= hi, f'{name}.length must be in [{lo}, {hi}]')
    need(set(value) <= set(alphabet), f'{name} characters must belong to {alphabet!r}')


def matrix(value, rlo, rhi, clo, chi, vlo, vhi, name):
    array(value, rlo, rhi, name)
    need(type(value[0]) is list, f'{name} rows must be arrays')
    width = len(value[0])
    for row in value:
        numbers(row, clo, chi, vlo, vhi, f'{name}[i]')
        need(len(row) == width, f'{name} must be rectangular')
    return len(value), width


def arity(args, count):
    need(type(args) is list and len(args) == count, f'argument list must contain exactly {count} entries')


def _time_options(s):
    return [f'{h:02}:{m:02}' for h in range(12) for m in range(60)
            if all(a == '?' or a == b for a, b in zip(s, f'{h:02}:{m:02}'))]


def _offsets(a, b):
    # Multiset containment proves that exactly len(a)-len(b)=2 deletions suffice.
    ca, cb = Counter(a), Counter(b)
    return [x for x in {min(b) - v for v in a}
            if all(ca[y - x] >= count for y, count in cb.items())]


def _permutation(encoded):
    n = len(encoded) + 1
    first = 0
    for value in range(1, n + 1):
        first ^= value
    for value in encoded[1::2]:
        first ^= value
    result = [first]
    for value in encoded:
        result.append(result[-1] ^ value)
    return result


# Comparison policies describe statements; they are not blanket permissions to
# bypass the runner's independent type/effect/alias checks.
COMPARISON_POLICIES = {
    472: 'set-of-strings', 767: 'same-character-multiset-with-no-equal-neighbors-or-proven-impossible',
    784: 'set-of-strings', 813: 'finite-number-absolute-error-1e-6',
    814: 'pruned-tree-topology', 876: 'original-middle-list-node',
    998: 'maximum-tree-topology', 1008: 'bst-preorder-topology',
    1203: 'valid-group-contiguous-topological-order-or-proven-impossible',
    1377: 'finite-number-absolute-error-1e-5', 1382: 'balanced-bst-with-identical-value-multiset',
    1489: 'ordered-pair-of-index-sets', 1548: 'minimum-mismatch-valid-graph-path',
    1606: 'set-of-server-indices', 1701: 'finite-number-absolute-error-1e-5',
    1901: 'any-strict-local-grid-peak', 1948: 'set-of-folder-paths',
    1982: 'array-whose-subset-sum-multiset-equals-input', 2007: 'valid-doubled-array-recovery-or-proven-impossible',
    2074: 'list-node-values', 2196: 'described-tree-topology',
    2733: 'any-input-value-except-minimum-and-maximum-or-minus-one',
    2807: 'list-node-values', 2816: 'list-node-values', 2933: 'set-of-strings',
}
EFFECT_POLICIES = {
    814: 'statement says same tree with zero-only subtrees removed; surviving original nodes may be reused',
    876: 'read-only; return must alias original node at floor(node_count/2)',
    998: 'new value appended to maximum-tree construction; existing nodes may be reused',
    1382: 'any balanced reconstruction with original values; topology is not uniquely specified',
    2074: 'statement requires reversing nodes in even-length groups and returning modified list',
    2807: 'statement requires inserting gcd-valued nodes between original adjacent nodes',
    2816: 'statement permits returned head after doubling; leading carry may need a new node',
}
EXTRA_IDS = frozenset((472,767,783,784,813,814,876,938,958,998,1008,1026,1203,
    1263,1293,1301,1305,1339,1372,1377,1382,1489,1548,1609,1901,1948,1982,
    2074,2196,2385,2583,2792,2807,2816))
DOMAIN_IDS = DOMAIN_IDS | EXTRA_IDS


def tree_nodes(encoded, nlo, nhi, vlo, vhi, name='root', bst=False, maximum=False):
    """Decode only topology, accepting semantically redundant trailing nulls.

    Node records are [value,left_index,right_index]; no candidate objects or
    implementation code are loaded. Orphan non-null values are never discarded.
    """
    if encoded is None:
        values=[]
    else:
        need(type(encoded) is dict and set(encoded)=={'__tree_node__'}, f'{name} must use __tree_node__ transport')
        values=encoded['__tree_node__']
        need(type(values) is list,f'{name} level-order transport must be an array')
    if not values or values[0] is None:
        need(all(v is None for v in values),f'{name} has non-null orphan nodes after null root')
        need(nlo==0,f'{name} node count must be in [{nlo}, {nhi}]')
        return []
    nodes=[[values[0],None,None]]; cursor=1; parent=0
    while parent<len(nodes) and cursor<len(values):
        for side in (1,2):
            if cursor>=len(values): break
            value=values[cursor]; cursor+=1
            if value is not None:
                nodes[parent][side]=len(nodes); nodes.append([value,None,None])
        parent+=1
    need(all(v is None for v in values[cursor:]),f'{name} has non-null orphan nodes after finished tree')
    need(nlo<=len(nodes)<=nhi,f'{name} node count must be in [{nlo}, {nhi}]')
    for value,_,_ in nodes: integer(value,vlo,vhi,f'{name}.Node.val')
    if bst:
        pending=[(0,None,None)]
        while pending:
            i,lo,hi=pending.pop(); value,left,right=nodes[i]
            need((lo is None or value>lo) and (hi is None or value<hi),f'{name} must satisfy strict BST ordering for all descendants')
            if left is not None: pending.append((left,lo,value))
            if right is not None: pending.append((right,value,hi))
    if maximum:
        need(len({node[0] for node in nodes})==len(nodes),f'{name} maximum-tree values are unique')
        for value,left,right in nodes:
            need(all(child is None or value>nodes[child][0] for child in (left,right)),f'{name} parent value exceeds all descendant values')
    return nodes


def list_values(encoded,nlo,nhi,vlo,vhi):
    need(type(encoded) is dict and set(encoded)=={'__list_node__'},'head must use __list_node__ transport')
    values=encoded['__list_node__']; numbers(values,nlo,nhi,vlo,vhi,'head.Node.val')
    return values


def graph(n,edges,tree=False,one_based=False,weighted=False,ordered=False):
    need(type(edges) is list,'edges must be an array')
    offset=1 if one_based else 0; parent=list(range(n)); pairs=set()
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]; x=parent[x]
        return x
    for edge in edges:
        array(edge,3 if weighted else 2,3 if weighted else 2,'edge')
        x,y=edge[:2]; integer(x,offset,n-1+offset,'edge endpoint'); integer(y,offset,n-1+offset,'edge endpoint')
        need(x!=y,'graph has no self loops')
        if ordered: need(x<y,'edge endpoints must satisfy ai < bi')
        key=tuple(sorted((x,y))); need(key not in pairs,'each undirected pair has at most one edge'); pairs.add(key)
        if weighted: integer(edge[2],1,1000,'edge weight')
        a,b=find(x-offset),find(y-offset)
        if tree: need(a!=b,'tree must not contain a cycle')
        parent[a]=b
    need(len({find(i) for i in range(n)})==1,'graph must be connected')


def recoverable_subset_sums(n,sums):
    """Witness-check the existence promise through nonnegative subset sums.

    Flipping all negative elements to positive translates every subset sum by
    -min(sums). Greedily recovering the smallest remaining positive magnitude
    is forced. A valid sign assignment exists iff -min(sums) is one of the
    recovered magnitude subset sums. This checks the promise, not a candidate.
    """
    minimum=min(sums); shifted=sorted(x-minimum for x in sums); counts=Counter(shifted)
    counts[0]-=1; formed=[0]; cursor=0
    for _ in range(n):
        while cursor<len(shifted) and not counts[shifted[cursor]]: cursor+=1
        if cursor==len(shifted): return False
        value=shifted[cursor]; added=[x+value for x in formed]
        required=Counter(added)
        if any(counts[x]<count for x,count in required.items()): return False
        counts.subtract(required); formed+=added
    return not any(counts.values()) and -minimum in formed


def _validate_extra(pid,args):
    arity(args,{813:2,938:3,998:2,1203:4,1293:2,1305:2,1377:4,1489:2,
                1548:4,1982:2,2385:2,2583:2,2792:2}.get(pid,1))
    a=args[0]
    tree_specs={783:(2,100,0,100000),814:(1,200,0,1),938:(1,20000,1,100000),
        958:(1,100,1,1000),998:(1,100,1,100),1026:(2,5000,0,100000),
        1339:(2,50000,1,10000),1372:(1,50000,1,100),1382:(1,10000,1,100000),
        1609:(1,100000,1,10**6),2385:(1,100000,1,100000),2583:(2,100000,1,10**6),
        2792:(1,10000,1,10000)}
    if pid in tree_specs:
        nodes=tree_nodes(a,*tree_specs[pid],bst=pid in (783,938,1382),maximum=pid==998)
        values=[row[0] for row in nodes]
        if pid==938:
            integer(args[1],1,100000,'low'); integer(args[2],args[1],100000,'high')
        elif pid==998:
            integer(args[1],1,100,'val'); need(args[1] not in values,'appended val is distinct from all tree values')
        elif pid==2385:
            need(len(set(values))==len(values),'tree values are unique'); integer(args[1],1,100000,'start'); need(args[1] in values,'a node with value start exists in tree')
        elif pid==2583: integer(args[1],1,len(nodes),'k')
        elif pid==2792: integer(args[1],1,10,'k')
    elif pid==1305:
        for i,value in enumerate(args): tree_nodes(value,0,5000,-100000,100000,f'root{i+1}',bst=True)
    elif pid in (876,2074,2807,2816):
        specs={876:(1,100,1,100),2074:(1,100000,0,100000),2807:(1,5000,1,1000),2816:(1,10000,0,9)}
        values=list_values(a,*specs[pid])
        if pid==2816: need(len(values)==1 or values[0]!=0,'list represents number without leading zeros except zero itself')
    elif pid==472:
        array(a,1,10000,'words')
        for word in a: text(word,1,30,LOWER,'words[i]')
        need(len(set(a))==len(a),'words are distinct'); need(sum(map(len,a))<=100000,'sum of word lengths <= 100000')
    elif pid==767: text(a,1,500,LOWER,'s')
    elif pid==784: text(a,1,12,LETTERS+string.digits,'s')
    elif pid==813:
        numbers(a,1,100,1,10000,'nums'); integer(args[1],1,len(a),'k')
    elif pid==1008:
        numbers(a,1,100,1,1000,'preorder',True); lower=None; stack=[]
        for value in a:
            need(lower is None or value>lower,'preorder must be a realizable strict BST preorder')
            while stack and stack[-1]<value: lower=stack.pop()
            stack.append(value)
    elif pid==1203:
        n,m,group,before=args; integer(n,1,30000,'n'); integer(m,1,n,'m'); numbers(group,n,n,-1,m-1,'group'); array(before,n,n,'beforeItems')
        for i,row in enumerate(before):
            numbers(row,0,n-1,0,n-1,'beforeItems[i]',True); need(i not in row,'item cannot precede itself')
    elif pid==1263:
        array(a,1,20,'grid'); width=None; counts=Counter()
        for row in a:
            array(row,1,20,'grid[i]')
            if width is None: width=len(row)
            need(len(row)==width,'grid is rectangular')
            for cell in row: text(cell,1,1,'.#STB','grid cell'); counts[cell]+=1
        need(all(counts[c]==1 for c in 'STB'),'grid has exactly one S, T, and B')
    elif pid==1293:
        h,w=matrix(a,1,40,1,40,0,1,'grid'); integer(args[1],1,h*w,'k'); need(a[0][0]==a[-1][-1]==0,'grid start and destination are empty')
    elif pid==1301:
        array(a,2,100,'board')
        for row in a: text(row,len(a),len(a),'123456789XES','board[i]')
        counts=Counter(''.join(a)); need(a[0][0]=='E' and a[-1][-1]=='S' and counts['E']==counts['S']==1,'only top-left E and bottom-right S; other cells are 1..9 or X')
    elif pid==1377:
        n,edges,t,target=args; integer(n,1,100,'n'); array(edges,n-1,n-1,'edges'); integer(t,1,50,'t'); integer(target,1,n,'target'); graph(n,edges,tree=True,one_based=True)
    elif pid==1489:
        n,edges=args; integer(n,2,100,'n'); array(edges,1,min(200,n*(n-1)//2),'edges'); graph(n,edges,weighted=True,ordered=True)
    elif pid==1548:
        n,roads,names,target=args; integer(n,2,100,'n'); array(roads,n-1,n*(n-1)//2,'roads'); graph(n,roads)
        array(names,n,n,'names'); array(target,1,100,'targetPath')
        for word in names+target: text(word,3,3,UPPER,'city name')
    elif pid==1901:
        h,w=matrix(a,1,500,1,500,1,100000,'mat')
        for r in range(h):
            for c in range(w):
                need((r==0 or a[r][c]!=a[r-1][c]) and (c==0 or a[r][c]!=a[r][c-1]),'no adjacent grid cells are equal')
    elif pid==1948:
        array(a,1,20000,'paths'); paths=set(); size=0
        for path in a:
            array(path,1,500,'paths[i]')
            for part in path: text(part,1,10,LOWER,'folder name'); size+=len(part)
            need(tuple(path) not in paths,'no two paths lead to same folder'); paths.add(tuple(path))
        need(size<=200000,'total folder-name characters <= 200000')
        need(all(len(path)==1 or path[:-1] in paths for path in paths),'each non-root folder parent is in input')
    elif pid==1982:
        n,sums=args; integer(n,1,15,'n'); numbers(sums,2**n,2**n,-10000,10000,'sums')
        need(recoverable_subset_sums(n,sums),'sums must be the full subset-sum multiset of at least one length-n integer array')
    elif pid==2196:
        array(a,1,10000,'descriptions'); children={}; parents={}; nodes=set()
        for row in a:
            array(row,3,3,'description'); p,c,left=row; integer(p,1,100000,'parent'); integer(c,1,100000,'child'); integer(left,0,1,'isLeft')
            # Repeating an identical declaration adds no contradictory edge.
            # The statement promises a valid tree, not distinct description rows.
            if children.get((p,left))==c and parents.get(c)==p:
                continue
            need(p!=c and c not in parents,'each child has exactly one parent and no self edge')
            need((p,left) not in children,'each parent has at most one left and one right child')
            children[p,left]=c; parents[c]=p; nodes.update((p,c))
        roots=nodes-parents.keys(); need(len(roots)==1,'descriptions have exactly one tree root')
        visited=set(); stack=list(roots)
        while stack:
            node=stack.pop(); need(node not in visited,'descriptions form an acyclic tree'); visited.add(node)
            stack.extend(children[node,side] for side in (0,1) if (node,side) in children)
        need(visited==nodes,'all described nodes belong to the single rooted tree')
    else: raise DomainError(f'missing extra validator for {pid}')


def validate(pid, args):
    """Validate the full declared input domain of a supported statement."""
    need(pid in DOMAIN_IDS, f'no independently reviewed domain validator for problem {pid}')
    if pid in EXTRA_IDS:
        return _validate_extra(pid,args)
    counts = {68:2,1283:2,1337:2,1383:4,1439:2,1444:2,1560:2,1575:4,
              1601:2,1606:3,1610:3,1639:2,1643:2,1681:2,1687:4,1703:2,
              1755:2,1775:2,2059:3,2109:2,2305:2,2311:2,2391:2,2399:2,
              2450:2,2457:2,2680:2,2817:2,2869:2,2937:3,3004:2,3013:3,
              3074:2,3132:2,3159:3,3218:4}
    arity(args, counts.get(pid, 1))
    a = args[0]
    if pid == 68:
        words, width = args
        array(words, 1, 300, 'words'); integer(width, 1, 100, 'maxWidth')
        for word in words:
            need(type(word) is str and 1 <= len(word) <= 20, 'words[i].length must be in [1, 20]')
            need(all(c.isprintable() and not c.isspace() and (not c.isalpha() or c in LETTERS) for c in word), 'words[i] consists of English letters and non-space symbols')
            need(len(word) <= width, 'words[i].length <= maxWidth')
    elif pid in (660,1256,1954,2231,2802,2847):
        bounds = {660:(1,800000000),1256:(0,10**9),1954:(1,10**15),
                  2231:(1,10**9),2802:(1,10**9),2847:(1,10**15)}
        integer(a, *bounds[pid], 'n')
    elif pid == 1283:
        numbers(a,1,50000,1,10**6,'nums'); integer(args[1],len(a),10**6,'threshold')
    elif pid == 1289:
        h,w = matrix(a,1,200,1,200,-99,99,'grid'); need(h == w,'grid must be square')
    elif pid == 1324:
        text(a,1,200,UPPER+' ','s'); need(re.fullmatch('[A-Z]+(?: [A-Z]+)*',a) is not None,'s has words separated by exactly one space and no edge spaces')
    elif pid == 1337:
        h,_ = matrix(a,2,100,2,100,0,1,'mat'); integer(args[1],1,h,'k')
        need(all(row == sorted(row,reverse=True) for row in a),'all soldiers (1) precede civilians (0) in each row')
    elif pid in (1356,1365,1395,1569,1711,1966,2007,2401,2403,2411,2562,2659,2733,2855,3079,3158,3194):
        spec = {1356:(1,500,0,10000,False),1365:(2,500,0,100,False),
            1395:(3,1000,1,100000,True),1569:(1,1000,1,len(a) if isinstance(a,list) else 0,True),
            1711:(1,100000,0,2**20,False),1966:(1,100000,-100000,100000,True),
            2007:(1,100000,0,100000,False),2401:(1,100000,1,10**9,False),
            2403:(1,17,1,10**9,False),2411:(1,100000,0,10**9,False),
            2562:(1,1000,1,10000,False),2659:(1,100000,-10**9,10**9,True),
            2733:(1,100,1,100,True),2855:(1,100,1,100,True),3079:(1,50,1,1000,False),
            3158:(1,50,1,50,False),3194:(2,50,1,50,False)}[pid]
        numbers(a,*spec[:4],'nums',distinct=spec[4])
        if pid == 3158:
            need(max(Counter(a).values()) <= 2,'each number appears once or twice')
        if pid == 3194:
            need(len(a)%2 == 0,'nums.length is even')
    elif pid == 1366:
        array(a,1,1000,'votes')
        for vote in a:
            text(vote,1,26,UPPER,'votes[i]')
            need(len(set(vote)) == len(vote),'all characters in each vote are unique')
            need(set(vote) == set(a[0]),'all votes contain the same teams')
    elif pid == 1383:
        n,speed,eff,k = args; integer(n,1,100000,'n'); integer(k,1,n,'k')
        numbers(speed,n,n,1,100000,'speed'); numbers(eff,n,n,1,10**8,'efficiency')
    elif pid == 1439:
        h,w = matrix(a,1,40,1,40,1,5000,'mat'); integer(args[1],1,min(200,w**h),'k')
        need(all(row == sorted(row) for row in a),'mat rows are non-decreasing')
    elif pid == 1444:
        array(a,1,50,'pizza')
        for row in a:
            text(row,1,50,'A.','pizza[i]'); need(len(row)==len(a[0]),'pizza must be rectangular')
        integer(args[1],1,10,'k')
    elif pid == 1554:
        # The published constraints specify total character count, not array size.
        array(a,0,100001,'dict')
        for word in a:
            text(word,0,100000,LOWER,'dict[i]'); need(len(word)==len(a[0]),'all dict strings have equal length')
        need(sum(map(len,a))<=100000,'total characters in dict <= 100000')
        need(len(set(a))==len(a),'dict strings are unique')
    elif pid == 1560:
        integer(a,2,100,'n'); numbers(args[1],2,101,1,a,'rounds')
        need(all(x!=y for x,y in zip(args[1],args[1][1:])),'consecutive rounds values differ')
    elif pid == 1575:
        numbers(a,2,100,1,10**9,'locations',True)
        integer(args[1],0,len(a)-1,'start'); integer(args[2],0,len(a)-1,'finish'); integer(args[3],1,200,'fuel')
    elif pid == 1601:
        integer(a,1,20,'n'); matrix(args[1],1,16,2,2,0,a-1,'requests')
    elif pid == 1606:
        integer(a,1,100000,'k'); numbers(args[1],1,100000,1,10**9,'arrival'); numbers(args[2],len(args[1]),len(args[1]),1,10**9,'load')
        need(all(x<y for x,y in zip(args[1],args[1][1:])),'arrival is strictly increasing')
    elif pid == 1610:
        matrix(a,1,100000,2,2,0,100,'points'); integer(args[1],0,359,'angle'); numbers(args[2],2,2,0,100,'location')
    elif pid == 1639:
        array(a,1,1000,'words')
        for word in a:
            text(word,1,1000,LOWER,'words[i]'); need(len(word)==len(a[0]),'all strings in words have the same length')
        text(args[1],1,1000,LOWER,'target')
    elif pid == 1643:
        numbers(a,2,2,1,15,'destination'); integer(args[1],1,comb(sum(a),a[0]),'k')
    elif pid == 1678:
        text(a,1,100,'G()al','command'); need(re.fullmatch(r'(?:G|\(\)|\(al\))+',a) is not None,'command consists of G, (), and/or (al) tokens')
    elif pid == 1681:
        numbers(a,1,16,1,len(a) if isinstance(a,list) else 0,'nums'); integer(args[1],1,len(a),'k'); need(len(a)%args[1]==0,'nums.length is divisible by k')
    elif pid == 1687:
        _,ports,boxes,weight=args
        for name,value in [('portsCount',ports),('maxBoxes',boxes),('maxWeight',weight)]: integer(value,1,100000,name)
        array(a,1,100000,'boxes')
        for box in a:
            array(box,2,2,'boxes[i]'); integer(box[0],1,ports,'port'); integer(box[1],1,weight,'weight')
    elif pid == 1701:
        matrix(a,1,100000,2,2,1,10000,'customers'); need(all(x[0]<=y[0] for x,y in zip(a,a[1:])),'customer arrivals are non-decreasing')
    elif pid == 1703:
        numbers(a,1,100000,0,1,'nums'); integer(args[1],1,sum(a),'k')
    elif pid == 1734:
        numbers(a,2,99998,0,131071,'encoded'); need(len(a)%2==0,'permutation length n is odd')
        need(set(_permutation(a)) == set(range(1,len(a)+2)),'encoded must encode a permutation of 1..n')
    elif pid == 1755:
        numbers(a,1,40,-10**7,10**7,'nums'); integer(args[1],-10**9,10**9,'goal')
    elif pid == 1775:
        numbers(a,1,100000,1,6,'nums1'); numbers(args[1],1,100000,1,6,'nums2')
    elif pid == 1859:
        text(a,2,200,LETTERS+' 123456789','s'); words=a.split(' ')
        need(1<=len(words)<=9 and all(re.fullmatch('[a-zA-Z]+[1-9]',w) for w in words),'each shuffled word consists of letters followed by its single position digit')
        need(sorted(int(w[-1]) for w in words)==list(range(1,len(words)+1)),'positions must be a permutation of 1..word_count')
    elif pid in (1915,1941,2268,2710,3120):
        spec={1915:(1,100000,'abcdefghij'),1941:(1,1000,LOWER),2268:(1,100000,LOWER),2710:(1,1000,string.digits),3120:(1,50,LETTERS)}[pid]
        text(a,*spec,'s')
        if pid==2710: need(a[0]!='0','num has no leading zeroes')
    elif pid == 2059:
        numbers(a,1,1000,-10**9,10**9,'nums',True); integer(args[1],0,1000,'start'); integer(args[2],-10**9,10**9,'goal'); need(args[1]!=args[2],'start != goal')
    elif pid == 2109:
        text(a,1,300000,LETTERS,'s'); numbers(args[1],1,300000,0,len(a)-1,'spaces')
        need(all(x<y for x,y in zip(args[1],args[1][1:])),'spaces are strictly increasing')
    elif pid == 2305:
        numbers(a,2,8,1,100000,'cookies'); integer(args[1],2,len(a),'k')
    elif pid == 2311:
        text(a,1,1000,'01','s'); integer(args[1],1,10**9,'k')
    elif pid == 2387:
        h,w=matrix(a,1,500,1,500,1,10**6,'grid'); need(h%2==w%2==1,'grid height and width are odd'); need(all(r==sorted(r) for r in a),'grid rows are non-decreasing')
    elif pid == 2391:
        array(a,2,100000,'garbage')
        for s in a: text(s,1,10,'MPG','garbage[i]')
        numbers(args[1],len(a)-1,len(a)-1,1,100,'travel')
    elif pid == 2399:
        text(a,2,52,LOWER,'s'); need(set(Counter(a).values())=={2},'each letter in s appears exactly twice'); numbers(args[1],26,26,0,50,'distance')
    elif pid == 2450:
        text(a,1,100000,'01','s'); integer(args[1],1,len(a),'k')
    elif pid == 2457:
        integer(a,1,10**12,'n'); integer(args[1],1,150,'target')
    elif pid == 2639:
        matrix(a,1,100,1,100,-10**9,10**9,'grid')
    elif pid == 2680:
        numbers(a,1,100000,1,10**9,'nums'); integer(args[1],1,15,'k')
    elif pid == 2744:
        array(a,1,50,'words')
        for s in a: text(s,2,2,LOWER,'words[i]')
        need(len(set(a))==len(a),'words are distinct')
    elif pid == 2817:
        numbers(a,1,100000,1,10**9,'nums'); integer(args[1],0,len(a)-1,'x')
    elif pid == 2869:
        numbers(a,1,50,1,len(a) if isinstance(a,list) else 0,'nums'); integer(args[1],1,len(a),'k')
        need(set(range(1,args[1]+1)) <= set(a),'input permits collecting every element 1..k')
    elif pid == 2933:
        array(a,1,100,'access_times')
        for row in a:
            array(row,2,2,'access_times[i]'); text(row[0],1,10,LOWER,'name'); text(row[1],4,4,string.digits,'time')
            need(int(row[1][:2])<24 and int(row[1][2:])<60,'access time is valid 24-hour HHMM')
    elif pid == 2937:
        for i,s in enumerate(args): text(s,1,100,LOWER,f's{i+1}')
    elif pid == 2965:
        h,w=matrix(a,2,50,2,50,1,2500,'grid'); need(h==w,'grid is square')
        values=[v for r in a for v in r]; need(max(values)<=h*h,'grid values <= n*n')
        counts=Counter(values); need(sorted(counts.values())==[1]*(h*h-2)+[2],'grid has exactly one duplicated value, one missing value, all others once')
    elif pid == 3004:
        edges,colors=args; array(edges,0,49999,'edges'); n=len(edges)+1; array(edges,n-1,n-1,'edges'); numbers(colors,n,n,1,100000,'colors')
        parent=list(range(n))
        def find(x):
            while parent[x]!=x:
                parent[x]=parent[parent[x]]; x=parent[x]
            return x
        for edge in edges:
            numbers(edge,2,2,0,n-1,'edge'); x,y=map(find,edge); need(x!=y,'edges represent a tree without cycles or self loops'); parent[x]=y
    elif pid == 3013:
        numbers(a,3,100000,1,10**9,'nums'); integer(args[1],3,len(a),'k'); integer(args[2],args[1]-2,len(a)-2,'dist')
    elif pid == 3074:
        numbers(a,1,50,1,50,'apple'); numbers(args[1],1,50,1,50,'capacity'); need(sum(a)<=sum(args[1]),'sum(capacity) >= sum(apple): redistribution must be possible')
    elif pid == 3114:
        text(a,5,5,'0123456789?:','s'); need(a[2]==':' and ':' not in a[:2]+a[3:],'only s[2] is colon'); need(bool(_time_options(a)),'at least one matching time exists between 00:00 and 11:59')
    elif pid == 3132:
        numbers(a,3,200,0,1000,'nums1'); numbers(args[1],len(a)-2,len(a)-2,0,1000,'nums2'); need(bool(_offsets(a,args[1])),'nums2 is reachable by deleting exactly two elements and adding one integer x')
    elif pid == 3159:
        numbers(a,1,100000,1,10000,'nums'); numbers(args[1],1,100000,1,100000,'queries'); integer(args[2],1,10000,'x')
    elif pid == 3167:
        text(a,1,60000,LOWER+string.digits,'compressed'); need(re.fullmatch(r'(?:[a-z][1-9][0-9]*)+',a) is not None,'compressed is character/frequency tokens without leading zeros')
        need(all(len(n)<=5 and int(n)<=10000 for n in re.findall(r'[0-9]+',a)),'each compressed frequency is in [1, 10000]')
    elif pid == 3218:
        m,n,h,v=args; integer(m,1,20,'m'); integer(n,1,20,'n'); numbers(h,m-1,m-1,1,1000,'horizontalCut'); numbers(v,n-1,n-1,1,1000,'verticalCut')
    else:
        raise DomainError(f'missing validator implementation for {pid}')


def expected(pid, args):
    """Independent statement-level oracle; rejects IDs with only domain review."""
    validate(pid,args)
    if pid not in ORACLE_IDS:
        raise ValueError(f'no independent answer oracle for {pid}')
    a=args[0]
    if pid==68:
        result=[]; start=0; words,width=args
        while start<len(words):
            end=start+1
            while end<len(words) and sum(map(len,words[start:end+1]))+end-start<=width: end+=1
            group=words[start:end]
            if end==len(words) or len(group)==1: line=' '.join(group).ljust(width)
            else:
                spaces,extra=divmod(width-sum(map(len,group)),len(group)-1)
                line=''.join(w+' '*(spaces+(i<extra)) for i,w in enumerate(group[:-1]))+group[-1]
            result.append(line); start=end
        return result
    if pid==660:
        digits=[]
        while a: a,d=divmod(a,9); digits.append(str(d))
        return int(''.join(reversed(digits)))
    if pid==1324:
        words=a.split(); return [''.join(w[i] if i<len(w) else ' ' for w in words).rstrip() for i in range(max(map(len,words)))]
    if pid==1337: return sorted(range(len(a)),key=lambda i:(sum(a[i]),i))[:args[1]]
    if pid==1356: return sorted(a,key=lambda n:(bin(n).count('1'),n))
    if pid==1365: return [sum(y<x for y in a) for x in a]
    if pid==1366:
        counts={c:tuple(-sum(v[i]==c for v in a) for i in range(len(a[0]))) for c in a[0]}
        return ''.join(sorted(a[0],key=lambda c:(counts[c],c)))
    if pid==1395:
        return sum(sum(x<b for x in a[:j])*sum(x>b for x in a[j+1:])+sum(x>b for x in a[:j])*sum(x<b for x in a[j+1:]) for j,b in enumerate(a))
    if pid==1560:
        first,last=args[1][0],args[1][-1]; return list(range(first,last+1)) if first<=last else list(range(1,last+1))+list(range(first,a+1))
    if pid==1569:
        # Root partitions are forced; all left/right insertion interleavings count.
        # Iterative postorder avoids recursion-depth assumptions at n=1000.
        stack=[(a,False)]; cache={}
        while stack:
            values,done=stack.pop(); key=tuple(values)
            if len(values)<2: cache[key]=1; continue
            left=[v for v in values[1:] if v<values[0]]; right=[v for v in values[1:] if v>values[0]]
            if done: cache[key]=comb(len(values)-1,len(left))*cache[tuple(left)]*cache[tuple(right)]%(10**9+7)
            else: stack.extend([(values,True),(left,False),(right,False)])
        return (cache[tuple(a)]-1)%(10**9+7)
    if pid==1643:
        row,col=a; k=args[1]; out=''
        while row or col:
            starts_h=comb(row+col-1,row) if col else 0
            if k<=starts_h: out+='H'; col-=1
            else: out+='V'; row-=1; k-=starts_h
        return out
    if pid==1678: return a.replace('()','o').replace('(al)','al')
    if pid==1701:
        end=total=0
        for arrival,cook in a: end=max(end,arrival)+cook; total+=end-arrival
        return total/len(a)
    if pid==1734: return _permutation(a)
    if pid==1859: return ' '.join(w[:-1] for w in sorted(a.split(),key=lambda w:w[-1]))
    if pid==1941: return len(set(Counter(a).values()))==1
    if pid==2109:
        positions=set(args[1]); return ''.join((' ' if i in positions else '')+c for i,c in enumerate(a))
    if pid==2231:
        odd=sorted((c for c in str(a) if int(c)%2),reverse=True); even=sorted((c for c in str(a) if not int(c)%2),reverse=True)
        streams={1:iter(odd),0:iter(even)}; return int(''.join(next(streams[int(c)%2]) for c in str(a)))
    if pid==2268: return sum(freq*(1+i//9) for i,freq in enumerate(sorted(Counter(a).values(),reverse=True)))
    if pid==2399: return all(a.rfind(c)-a.find(c)-1==args[1][ord(c)-97] for c in set(a))
    if pid==2450:
        # Each of n-k+1 flip vectors has a unique first nonzero position, hence
        # they are independent over GF(2). The generated subspace has 2^rank.
        return pow(2,len(a)-args[1]+1,10**9+7)
    if pid==2562:
        return sum(int(str(a[i])+str(a[-i-1])) for i in range(len(a)//2))+(a[len(a)//2] if len(a)%2 else 0)
    if pid==2639: return [max(len(str(row[c])) for row in a) for c in range(len(a[0]))]
    if pid==2710: return a.rstrip('0')
    if pid==2744: return sum(a[i]==a[j][::-1] for i in range(len(a)) for j in range(i+1,len(a)))
    if pid==2802:
        width=1; rank=a
        while rank>2**width: rank-=2**width; width+=1
        return format(rank-1,f'0{width}b').translate(str.maketrans('01','47'))
    if pid==2855:
        for k in range(len(a)):
            rotated=a[-k:]+a[:-k] if k else a
            if rotated==sorted(a): return k
        return -1
    if pid==2869:
        seen=set()
        for count,x in enumerate(reversed(a),1):
            if x<=args[1]: seen.add(x)
            if len(seen)==args[1]: return count
    if pid==2933:
        times=defaultdict(list)
        for name,time in a: times[name].append(60*int(time[:2])+int(time[2:]))
        return sorted(name for name,values in times.items() if any(y-x<60 for x,y in zip(sorted(values),sorted(values)[2:])))
    if pid==2937:
        prefix=0
        for chars in zip(*args):
            if len(set(chars))!=1: break
            prefix+=1
        return sum(map(len,args))-3*prefix if prefix else -1
    if pid==2965:
        counts=Counter(v for row in a for v in row); return [next(k for k,v in counts.items() if v==2),next(v for v in range(1,len(a)**2+1) if not counts[v])]
    if pid==3074:
        need_apples=sum(a)
        for count,capacity in enumerate(sorted(args[1],reverse=True),1):
            need_apples-=capacity
            if need_apples<=0: return count
    if pid==3079: return sum(int(max(str(v))*len(str(v))) for v in a)
    if pid==3114: return max(_time_options(a))
    if pid==3120: return len(set(a)&set(LOWER)&set(c.lower() for c in a if c in UPPER))
    if pid==3132: return min(_offsets(a,args[1]))
    if pid==3158:
        out=0
        for v,c in Counter(a).items():
            if c==2: out^=v
        return out
    if pid==3159:
        positions=[i for i,v in enumerate(a) if v==args[2]]; return [positions[q-1] if q<=len(positions) else -1 for q in args[1]]
    if pid==3167:
        counts=Counter()
        for letter,num in re.findall(r'([a-z])([0-9]+)',a): counts[letter]+=int(num)
        return ''.join(c+str(counts[c]) for c in sorted(counts))
    if pid==3194:
        values=sorted(a); return min((values[i]+values[-i-1])/2 for i in range(len(a)//2))
    if pid==3218:
        # Exhaustive cut-order dynamic programming over sorted cost prefixes.
        # For each orientation exchanging a cheaper-before-dearer pair can only
        # increase cost, so an optimal order sorts each orientation descending.
        h=sorted(args[2],reverse=True); v=sorted(args[3],reverse=True)
        dp=[[0]*(len(v)+1) for _ in range(len(h)+1)]
        for i in range(len(h)+1):
            for j in range(len(v)+1):
                if i or j: dp[i][j]=min(([dp[i-1][j]+h[i-1]*(j+1)] if i else [])+([dp[i][j-1]+v[j-1]*(i+1)] if j else []))
        return dp[-1][-1]
    raise AssertionError('oracle implementation missing')


def exact(a,b):
    if type(a) is not type(b): return False
    if isinstance(a,list): return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    if isinstance(a,dict): return a.keys()==b.keys() and all(exact(a[k],b[k]) for k in a)
    return a==b


def admit_case(pid, case):
    """Return provenance-preserving decision; no silent filtering or replacement."""
    original=deepcopy(case)
    try:
        need(type(case) is dict and set(case)=={'args','expected','compare'},'case fields must be args, expected, compare')
        need(case['compare']=='return','only return comparisons are supported')
        validate(pid,case['args'])
    except DomainError as error:
        return {'status':'rejected-domain','reason':str(error),'original':original}
    if pid not in ORACLE_IDS:
        return {'status':'domain-valid-oracle-unreviewed','original':original}
    wanted=expected(pid,case['args'])
    corrected=deepcopy(case); corrected['expected']=wanted
    equal=exact(wanted,case['expected'])
    if pid==2933 and isinstance(case['expected'],list):
        equal=exact(wanted,sorted(case['expected']))
    return {'status':'oracle-confirmed' if equal else 'oracle-corrected','original':original,
            'case':corrected,'comparison_policy':'set-of-strings' if pid==2933 else 'float-1e-5' if pid==1701 else 'exact',
            'reason':'expected value independently recomputed from pinned statement; no candidate output consulted'}


def public_domains(pid, raw):
    """Check statement examples against input validators, including typed nodes."""
    cleaned=html.unescape(re.sub('<[^>]*>','',raw.decode())).replace('\xa0',' ')
    checked=[]
    class Names(ast.NodeTransformer):
        def visit_Name(self,node):
            if node.id not in ('true','false','null'): raise ValueError('unsupported example token')
            return ast.copy_location(ast.Constant({'true':True,'false':False,'null':None}[node.id]),node)
    for match in re.finditer(r'Input:\s*(.*?)\s*Output:',cleaned,re.S):
        call=ast.parse('f('+match[1].strip()+')',mode='eval').body
        if not isinstance(call,ast.Call) or call.args or not call.keywords or any(k.arg is None for k in call.keywords): raise ValueError('unsupported public argument syntax')
        args=[ast.literal_eval(Names().visit(k.value)) for k in call.keywords]
        if pid in (783,814,938,958,998,1026,1339,1372,1382,1609,2385,2583,2792):
            args[0]={'__tree_node__':args[0]} if args[0] is not None else None
        if pid==1305:
            args=[{'__tree_node__':value} if value is not None else None for value in args]
        if pid in (876,2074,2807,2816): args[0]={'__list_node__':args[0]}
        validate(pid,args); checked.append(args)
    if not checked: raise ValueError(f'no public input example found for {pid}')
    return checked


def public_examples(pid, raw):
    """Cross-check each parseable statement example, failing on unsupported syntax."""
    cleaned=re.sub(r'</?(?:p|pre|div|li|ul|ol|br)\b[^>]*>','\n',raw.decode())
    cleaned=html.unescape(re.sub('<[^>]*>','',cleaned)).replace('\xa0',' ')
    class Names(ast.NodeTransformer):
        def visit_Name(self,node):
            if node.id not in ('true','false','null'): raise ValueError('unsupported example token')
            return ast.copy_location(ast.Constant({'true':True,'false':False,'null':None}[node.id]),node)
    checked=[]
    for m in re.finditer(r'Input:\s*(.*?)\s*Output:\s*(.*?)(?=Explanation:|Explantion:|Example\s*\d+:|Constraints:|$)',cleaned,re.S):
        call=ast.parse('f('+m[1].strip()+')',mode='eval').body
        if not isinstance(call,ast.Call) or call.args or not call.keywords or any(k.arg is None for k in call.keywords): raise ValueError('unsupported example arguments')
        args=[ast.literal_eval(Names().visit(k.value)) for k in call.keywords]
        want=ast.literal_eval(Names().visit(ast.parse(m[2].strip(),mode='eval')).body)
        got=expected(pid,args)
        same=exact(got,want)
        if pid in (1701,3194): same=type(want) in (int,float) and abs(got-want)<=1e-5
        if pid==2933: same=exact(got,sorted(want))
        if not same: raise ValueError(f'oracle disagrees with public example: {pid}: {got!r} != {want!r}')
        checked.append({'args':args,'expected':got,'compare':'return'})
    if not checked: raise ValueError(f'no public example found for {pid}')
    return checked


def digest(raw): return hashlib.sha256(raw).hexdigest()


def audit(freeze, gate_path, output):
    """Recheck permissions before every statement/case open; write no candidates."""
    from .boundary_policy import authorize_before_open
    gate=json.loads(Path(gate_path).read_text())
    freeze=Path(freeze); contract_raw=(freeze/'contract.json').read_bytes()
    if digest(contract_raw)!='956e15f937b9f457014eaac7d91939209ba3901f3f4f5f9e93b53f41ed037e43':
        raise ValueError('this admission audit requires the exact original freeze-v1 contract')
    contract=json.loads(contract_raw)
    jobs={row['id']:row for row in contract['jobs'] if row['id'] in DOMAIN_IDS}
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    report={'schema':'gamma.imported-case-admission.v1','module_sha256':digest(Path(__file__).read_bytes()),
            'freeze_contract_sha256':digest((freeze/'contract.json').read_bytes()),
            'automatic_promotion':False,'new_qualifications':0,'problems':[]}
    for pid,job in sorted(jobs.items()):
        authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language='python',payload_kind='statement')
        statement=Path(job['statement']['path']).read_bytes()
        if digest(statement)!=job['statement']['sha256']: raise ValueError('statement drift')
        domain_examples=public_domains(pid,statement)
        examples=public_examples(pid,statement) if pid in ORACLE_IDS else []
        authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language='python')
        raw=(freeze/job['tests']).read_bytes()
        if len(raw)>8*1024**2 or digest(raw)!=job['tests_raw_sha256']: raise ValueError('test payload drift/size')
        cases=json.loads(raw); decisions=[dict(index=i,**admit_case(pid,case)) for i,case in enumerate(cases)]
        data={'problem_id':pid,'statement':job['statement'],'original_tests_sha256':digest(raw),
              'public_examples_checked':examples,'public_domains_checked':domain_examples,
              'comparison_policy':COMPARISON_POLICIES.get(pid,'exact'),
              'effect_policy':EFFECT_POLICIES.get(pid,'no statement-specific mutation or alias permission declared here'),
              'decisions':decisions}
        encoded=json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'
        (output/f'{pid}.json').write_bytes(encoded)
        report['problems'].append({'id':pid,'case_count':len(cases),'public_examples':len(examples),
            'public_domains_checked':len(domain_examples),
            'counts':dict(Counter(d['status'] for d in decisions)),
            'rejection_reasons':dict(Counter(d['reason'] for d in decisions if d['status']=='rejected-domain')),
            'artifact':f'{pid}.json','sha256':digest(encoded)})
    report['counts']=dict(sum((Counter(row['counts']) for row in report['problems']),Counter()))
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze',required=True); parser.add_argument('--gate',dest='gate_path',required=True); parser.add_argument('--output',required=True)
    result=audit(**vars(parser.parse_args()))
    print(json.dumps({'problems':len(result['problems']),'counts':result['counts']}))
