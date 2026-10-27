"""Deterministic development tests; no network, private cases or promotion."""
from collections import Counter, deque
from copy import deepcopy
from functools import lru_cache
from itertools import combinations, permutations, product
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import random
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
IDS = [3227, 3234, 3242, 3513, 3522, 3527, 3534, 3546, 3556, 3562,
       3572, 3577, 3584, 3590, 3600, 3613, 3620]
RNG = random.Random(25204)
CASES = {pid: [] for pid in IDS}

def add(pid, args, expected, kind='independent_small_oracle'):
    CASES[pid].append({'args': args, 'expected': expected, 'kind': kind})

def example(pid, args, expected):
    add(pid, args, expected, 'public_example')

example(3227, ['leetcoder'], True)
example(3227, ['bbcd'], False)
example(3234, ['00011'], 5)
example(3234, ['101101'], 16)
example(3242, [['NeighborSum','adjacentSum','adjacentSum','diagonalSum','diagonalSum'],
               [[[[0,1,2],[3,4,5],[6,7,8]]],[1],[4],[4],[8]]], [None,6,16,16,4])
example(3242, [['NeighborSum','adjacentSum','diagonalSum'],
               [[[[1,2,0,3],[4,7,15,6],[8,9,10,11],[12,13,14,5]]],[15],[9]]], [None,23,45])
example(3513, [[1,2]], 2)
example(3513, [[3,1,2]], 4)
example(3522, [['jump','add','add','jump','add','jump'], [2,1,3,1,-2,-3]], 1)
example(3522, [['jump','add','add'], [3,1,1]], 0)
example(3522, [['jump'], [0]], 0)
example(3527, [[['good','ok','good','ok'],['ok','bad','good','ok','ok'],['good'],['bad']]], 'good')
example(3527, [[['good','ok','good'],['ok','bad'],['bad','notsure'],['great','good']]], 'bad')
example(3534, [5,[1,8,3,4,2],3,[[0,3],[2,4]]], [1,1])
example(3534, [5,[5,3,1,9,10],2,[[0,1],[0,2],[2,3],[4,3]]], [1,2,-1,1])
example(3534, [3,[3,6,1],1,[[0,0],[0,1],[1,2]]], [0,-1,-1])
example(3546, [[[1,4],[2,3]]], True)
example(3546, [[[1,3],[2,4]]], False)
example(3556, ['12234'], 1469)
example(3556, ['111'], 11)
example(3562, [2,[1,2],[4,3],[[1,2]],3], 5)
example(3562, [2,[3,4],[5,8],[[1,2]],4], 4)
example(3562, [3,[4,6,8],[7,9,11],[[1,2],[1,3]],10], 10)
example(3562, [3,[5,2,3],[8,5,6],[[1,2],[2,3]],7], 12)
example(3572, [[1,2,1,3,2],[5,3,4,6,2]], 14)
example(3572, [[1,2,1,2],[4,5,6,7]], -1)
example(3577, [[1,2,3]], 2)
example(3577, [[3,3,3,4,4,4]], 0)
example(3584, [[-1,-9,2,3,-2,-3,1],1], 81)
example(3584, [[1,3,-5,5,6,-4],3], 20)
example(3584, [[2,-1,2,-6,5,2,-5,7],2], 35)
example(3590, [[-1,0,0],[1,1,1],[[0,1],[0,2],[0,3]]], [0,1,-1])
example(3590, [[-1,0,1],[5,2,7],[[0,1],[1,2],[1,3],[2,1]]], [0,7,-1,0])
example(3600, [3,[[0,1,2,1],[1,2,3,0]],1], 2)
example(3600, [3,[[0,1,4,0],[1,2,3,0],[0,2,1,0]],2], 6)
example(3600, [3,[[0,1,1,1],[1,2,1,1],[2,0,1,1]],0], -1)
example(3613, [5,[[0,1,4],[1,2,3],[1,3,2],[3,4,6]],2], 4)
example(3613, [4,[[0,1,5],[1,2,5],[2,3,5]],1], 5)
example(3620, [[[0,1,5],[1,3,10],[0,2,3],[2,3,4]],[True]*4,10], 3)
example(3620, [[[0,1,7],[1,4,5],[0,2,6],[2,3,6],[3,4,2],[2,4,6]],
               [True,True,True,False,True],12], 6)

@lru_cache(None)
def game(s, turn):
    for left in range(len(s)):
        vowels = 0
        for right in range(left, len(s)):
            vowels += s[right] == 'a'
            if vowels % 2 == (1 if turn == 0 else 0):
                if not game(s[:left] + s[right+1:], 1-turn):
                    return True
    return False

for n in range(1, 8):
    for chars in product('ab', repeat=n):
        s = ''.join(chars)
        add(3227, [s], game(s, 0))
for n in range(1, 10):
    for chars in product('01', repeat=n):
        s = ''.join(chars)
        answer = 0
        for left in range(n):
            for right in range(left+1, n+1):
                ones = s[left:right].count('1')
                answer += ones >= (right-left-ones)**2
        add(3234, [s], answer)
for _ in range(35):
    n = RNG.randint(3, 10)
    flat = list(range(n*n)); RNG.shuffle(flat)
    grid = [flat[r*n:(r+1)*n] for r in range(n)]
    operations = ['NeighborSum']; arguments = [[grid]]; answers = [None]
    for value in range(n*n):
        for operation in ('adjacentSum', 'diagonalSum'):
            operations.append(operation); arguments.append([value])
            r, c = divmod(flat.index(value), n)
            answers.append(sum(grid[a][b] for a in range(n) for b in range(n)
                               if (abs(a-r)+abs(b-c)==1 if operation=='adjacentSum'
                                   else abs(a-r)==abs(b-c)==1)))
    add(3242, [operations, arguments], answers)
for n in range(1, 17):
    for _ in range(5):
        nums = list(range(1,n+1)); RNG.shuffle(nums)
        answer = len({nums[i]^nums[j]^nums[k] for i in range(n)
                      for j in range(i,n) for k in range(j,n)})
        add(3513, [nums], answer)
for _ in range(80):
    n = RNG.randint(1,25)
    instructions = [RNG.choice(['add','jump']) for _ in range(n)]
    values = [RNG.randint(-n,n) for _ in range(n)]
    index = score = 0; path = []
    for _ in range(n):
        if not 0 <= index < n or index in path: break
        path.append(index)
        if instructions[index]=='add': score += values[index]; index += 1
        else: index += values[index]
    add(3522, [instructions,values], score)
for _ in range(80):
    responses = [[RNG.choice(['a','aa','b','abc','z']) for _ in range(RNG.randint(1,8))]
                 for _ in range(RNG.randint(1,8))]
    words = {word for row in responses for word in row}
    best = min(words, key=lambda word:(-sum(word in row for row in responses),word))
    add(3527, [responses], best)
for _ in range(100):
    n = RNG.randint(1,20); values = [RNG.randint(0,30) for _ in range(n)]
    diff = RNG.randint(0,10); queries = [[RNG.randrange(n),RNG.randrange(n)] for _ in range(20)]
    answers = []
    for start, target in queries:
        distance = [-1]*n; distance[start]=0; queue=deque([start])
        while queue:
            u=queue.popleft()
            for v in range(n):
                if distance[v]<0 and abs(values[u]-values[v])<=diff:
                    distance[v]=distance[u]+1; queue.append(v)
        answers.append(distance[target])
    add(3534,[n,values,diff,queries],answers)
for _ in range(80):
    m,n=RNG.randint(1,5),RNG.randint(1,5)
    if m*n==1: n=2
    grid=[[RNG.randint(1,10) for _ in range(n)] for _ in range(m)]
    answer = any(sum(sum(row) for row in grid[:r])==sum(sum(row) for row in grid[r:]) for r in range(1,m))
    answer |= any(sum(sum(row[:c]) for row in grid)==sum(sum(row[c:]) for row in grid) for c in range(1,n))
    add(3546,[grid],answer)

def prime_miller(number):
    if number < 2: return False
    for p in (2,3,5,7,11,13):
        if number%p==0: return number==p
    d=number-1; exponent=0
    while d%2==0: d//=2; exponent+=1
    # These bases are deterministic far beyond this problem's 10-digit domain.
    for base in (2,3,5,7,11,13,17):
        x=pow(base,d,number)
        if x in (1,number-1): continue
        for _ in range(exponent-1):
            x=x*x%number
            if x==number-1: break
        else: return False
    return True
for _ in range(80):
    s=''.join(str(RNG.randrange(10)) for _ in range(RNG.randint(1,10)))
    primes={int(s[a:b]) for a in range(len(s)) for b in range(a+1,len(s)+1)
            if prime_miller(int(s[a:b]))}
    add(3556,[s],sum(sorted(primes,reverse=True)[:3]))
for _ in range(90):
    n=RNG.randint(1,9); present=[RNG.randint(1,12) for _ in range(n)]; future=[RNG.randint(1,16) for _ in range(n)]
    labels=list(range(1,n)); RNG.shuffle(labels); order=[0]+labels
    parent=[-1]*n
    for i in range(1,n): parent[order[i]]=order[RNG.randrange(i)]
    hierarchy=[[parent[u]+1,u+1] for u in range(1,n)]; RNG.shuffle(hierarchy)
    budget=RNG.randint(1,25); answer=0
    for mask in range(1<<n):
        spent=profit=0
        for u in range(n):
            if mask>>u&1:
                cost=present[u]//2 if parent[u]>=0 and mask>>parent[u]&1 else present[u]
                spent+=cost; profit+=future[u]-cost
        if spent<=budget: answer=max(answer,profit)
    add(3562,[n,present,future,hierarchy,budget],answer)
for _ in range(80):
    n=RNG.randint(3,10); x=[RNG.randint(1,6) for _ in range(n)]; y=[RNG.randint(1,30) for _ in range(n)]
    answer=max((sum(y[i] for i in indices) for indices in combinations(range(n),3)
                if len({x[i] for i in indices})==3),default=-1)
    add(3572,[x,y],answer)
for _ in range(70):
    n=RNG.randint(2,7); values=[RNG.randint(1,8) for _ in range(n)]; count=0
    for tail in permutations(range(1,n)):
        unlocked={0}
        for u in tail:
            if not any(v<u and values[v]<values[u] for v in unlocked): break
            unlocked.add(u)
        else: count+=1
    add(3577,[values],count)
for _ in range(80):
    n=RNG.randint(1,10); nums=[RNG.randint(-20,20) for _ in range(n)]; m=RNG.randint(1,n)
    answer=max(nums[idx[0]]*nums[idx[-1]] for idx in combinations(range(n),m))
    add(3584,[nums,m],answer)
for _ in range(100):
    n=RNG.randint(1,30); labels=list(range(1,n)); RNG.shuffle(labels); order=[0]+labels; par=[-1]*n
    children=[[] for _ in range(n)]
    for i in range(1,n):
        u=order[i]; par[u]=order[RNG.randrange(i)]; children[par[u]].append(u)
    vals=[RNG.randrange(32) for _ in range(n)]; xor=[0]*n
    for u in order: xor[u]=vals[u]^(xor[par[u]] if par[u]>=0 else 0)
    queries=[[RNG.randrange(n),RNG.randint(1,n)] for _ in range(25)]; answer=[]
    for u,k in queries:
        nodes=[u]
        for v in nodes: nodes.extend(children[v])
        distinct=sorted({xor[v] for v in nodes})
        answer.append(distinct[k-1] if k<=len(distinct) else -1)
    add(3590,[par,vals,queries],answer)

def components(n,edges):
    neighbors=[[] for _ in range(n)]
    for u,v,*_ in edges: neighbors[u].append(v); neighbors[v].append(u)
    unseen=set(range(n)); count=0
    while unseen:
        count+=1; queue=[unseen.pop()]
        for u in queue:
            for v in neighbors[u]:
                if v in unseen: unseen.remove(v); queue.append(v)
    return count
for _ in range(100):
    n=RNG.randint(2,6); pairs=list(combinations(range(n),2)); RNG.shuffle(pairs)
    edges=[[u,v,RNG.randint(1,10),int(RNG.random()<.25)] for u,v in pairs[:RNG.randint(1,min(9,len(pairs)))]]
    k=RNG.randint(0,n); answer=-1; mandatory={i for i,e in enumerate(edges) if e[3]}
    for tree_indices in combinations(range(len(edges)),n-1):
        if not mandatory<=set(tree_indices): continue
        tree=[edges[i] for i in tree_indices]
        if components(n,tree)!=1: continue
        optional=[i for i,e in enumerate(tree) if not e[3]]
        for count in range(min(k,len(optional))+1):
            for upgraded in combinations(optional,count):
                score=min(e[2]*(2 if i in upgraded else 1) for i,e in enumerate(tree))
                answer=max(answer,score)
    add(3600,[n,edges,k],answer)
for _ in range(80):
    n=RNG.randint(1,6); pairs=list(combinations(range(n),2)); RNG.shuffle(pairs)
    selected={(u,RNG.randrange(u)) for u in range(1,n)}
    selected={tuple(sorted(pair)) for pair in selected}
    for pair in pairs:
        if len(selected)<8 and RNG.random()<.3: selected.add(pair)
    edges=[[u,v,RNG.randint(1,15)] for u,v in selected]; k=RNG.randint(1,n); answer=math.inf
    for mask in range(1<<len(edges)):
        retained=[e for i,e in enumerate(edges) if mask>>i&1]
        if components(n,retained)<=k: answer=min(answer,max((e[2] for e in retained),default=0))
    add(3613,[n,edges,k],answer)
for _ in range(100):
    n=RNG.randint(2,9); order=list(range(n)); RNG.shuffle(order)
    edges=[[order[i],order[j],RNG.randint(0,15)] for i in range(n) for j in range(i+1,n) if RNG.random()<.35]
    online=[RNG.random()<.75 for _ in range(n)]; online[0]=online[-1]=True; k=RNG.randint(0,35)
    graph=[[] for _ in range(n)]
    for u,v,c in edges: graph[u].append((v,c))
    answer=-1; stack=[(0,0,math.inf)]
    while stack:
        u,cost,score=stack.pop()
        if u==n-1: answer=max(answer,score)
        for v,c in graph[u]:
            if online[v] and cost+c<=k: stack.append((v,cost+c,min(score,c)))
    add(3620,[edges,online,k],answer)

# Selected maximum-constraint shapes have independently computed closed forms.
add(3234,['1'*40000],40000*40001//2,'structured_large')
add(3513,[list(range(1,100001))],131072,'structured_large')
add(3522,[['add']*100000,[100000]*100000],10**10,'structured_large')
add(3534,[100000,list(range(100000)),1,[[0,99999],[50000,0],[20,20]]],[99999,50000,0],'structured_large')
add(3546,[[[100000]*100000]],True,'structured_large')
add(3577,[[1]+[2]*99999],math.factorial(99999)%1000000007,'structured_large')
add(3584,[[-100000]*100000,2],10**10,'structured_large')
add(3590,[[-1]+list(range(49999)),[1]*50000,[[0,1],[0,2],[0,3],[49999,1]]],[0,1,-1,0],'structured_large')
add(3600,[10000,[[i,i+1,100000,0] for i in range(9999)],9999],200000,'structured_large')
add(3613,[10000,[[i,i+1,999999] for i in range(9999)],1],999999,'structured_large')
add(3620,[[[i,i+1,10**9] for i in range(9999)],[True]*10000,9999*10**9],10**9,'structured_large')


def main():
    results=[]
    for pid in IDS:
        py_path=ROOT/'python'/f'{pid}.py'; js_path=ROOT/'javascript'/f'{pid}.js'
        compile(py_path.read_text(),str(py_path),'exec')
        subprocess.run(['node','--check',str(js_path)],check=True,capture_output=True,timeout=15)
        spec=importlib.util.spec_from_file_location(f'candidate_{pid}',py_path)
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        for index,case in enumerate(CASES[pid]):
            args=deepcopy(case['args']); before=deepcopy(args)
            actual=module.solve(*args)
            assert actual==case['expected'], ('python',pid,index,actual,case['expected'])
            assert args==before, ('python input mutation',pid,index)
        # Send arguments only to the child; expected answers remain in this driver.
        requests=[{'id':pid,'args':case['args']} for case in CASES[pid]]
        response=subprocess.run(['node',str(HERE/'runner.js')],input=json.dumps(requests),text=True,
                                capture_output=True,check=True,timeout=90)
        actuals=json.loads(response.stdout)
        assert len(actuals)==len(CASES[pid])
        for index,(actual,case) in enumerate(zip(actuals,CASES[pid])):
            assert actual['result']==case['expected'], ('javascript',pid,index,actual,case['expected'])
            assert actual['unchanged'], ('javascript input mutation',pid,index)
        counts=dict(Counter(case['kind'] for case in CASES[pid]))
        results.append({'problem_id':pid,'cases_per_language':len(CASES[pid]),'kinds':counts,
                        'python_pass':True,'javascript_pass':True,
                        'source_sha256':{lang:hashlib.sha256((ROOT/lang/f'{pid}.{ext}').read_bytes()).hexdigest()
                                         for lang,ext in [('python','py'),('javascript','js')]}})
        print(pid,len(CASES[pid]),'cases per language passed',flush=True)
    receipt={'schema':'gamma.request-252-batch4-development-tests.v1','seed':25204,
             'base_commit':'bc252ef318b165396288cd3f3d0ecbd4b84c03da',
             'cases_per_language':sum(len(cases) for cases in CASES.values()),
             'combined_language_checks':2*sum(len(cases) for cases in CASES.values()),
             'syntax_checks':2*len(IDS),'qualification':'not_qualified',
             'source_access_policy_changed':False,'results':results,
             'runtime':{'python':sys.version.split()[0], 'node':subprocess.check_output(['node','--version'],text=True).strip()},
             'test_driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'javascript_runner_sha256':hashlib.sha256((HERE/'runner.js').read_bytes()).hexdigest()}
    (HERE/'test-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({key:receipt[key] for key in ('cases_per_language','combined_language_checks','syntax_checks')}))

if __name__=='__main__': main()
