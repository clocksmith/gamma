"""Deterministic development evidence; no judge qualification or protected tests."""
from collections import Counter, deque
from functools import lru_cache
from itertools import combinations, permutations, product
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import math
import platform
import random
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
IDS = [3217,3231,3237,3484,3517,3524,3531,3539,3551,3559,3567,3574,3579,3587,3598,3608,3618]
MOD = 1_000_000_007
CASES = []
RNG = random.Random(252002)


def add(pid, args, expected, category='independent_small_oracle'):
    CASES.append(dict(problem_id=pid, args=args, expected=expected, category=category))


def oracle3231(nums):
    n = len(nums)
    chains = []
    for mask in range(1, 1 << n):
        values = [nums[i] for i in range(n) if mask >> i & 1]
        if all(a < b for a, b in zip(values, values[1:])):
            chains.append(mask)
    @lru_cache(None)
    def cover(mask):
        if not mask:
            return 0
        first = mask & -mask
        return min(1 + cover(mask ^ chain) for chain in chains
                   if chain & first and chain & mask == chain)
    return cover((1 << n) - 1)


def oracle3539(m, k, nums):
    return sum(math.prod(nums[index] for index in sequence)
               for sequence in product(range(len(nums)), repeat=m)
               if sum(1 << index for index in sequence).bit_count() == k) % MOD


def oracle3551(nums):
    target = tuple(sorted(nums, key=lambda x: (sum(map(int, str(x))), x)))
    initial = tuple(nums)
    queue, seen = deque([(initial, 0)]), {initial}
    while queue:
        current, distance = queue.popleft()
        if current == target:
            return distance
        for a, b in combinations(range(len(nums)), 2):
            following = list(current)
            following[a], following[b] = following[b], following[a]
            following = tuple(following)
            if following not in seen:
                seen.add(following)
                queue.append((following, distance + 1))


def oracle3559(edges, queries):
    adjacency = [[] for _ in range(len(edges) + 2)]
    for u, v in edges:
        adjacency[u].append(v)
        adjacency[v].append(u)
    result = []
    for source, target in queries:
        queue, seen = deque([(source, 0)]), {source}
        while queue:
            u, distance = queue.popleft()
            if u == target:
                result.append(sum(sum(weights) % 2 for weights in product([1, 2], repeat=distance)))
                break
            for v in adjacency[u]:
                if v not in seen:
                    seen.add(v)
                    queue.append((v, distance + 1))
    return result


def oracle3574(nums, k):
    best = 0
    for mask in range(1 << len(nums)):
        if mask.bit_count() > k:
            continue
        modified = [value * (2 if mask >> i & 1 else 1) for i, value in enumerate(nums)]
        for left in range(len(nums)):
            for right in range(left + 1, len(nums) + 1):
                best = max(best, (right - left) * math.gcd(*modified[left:right]))
    return best


@lru_cache(None)
def oracle_segment(first, second):
    # Enumerate every disjoint swap matching, not only reciprocal mismatches.
    answer = len(first)
    for reverse in (False, True):
        initial = list(first[::-1] if reverse else first)
        def match(remaining, current, swaps):
            nonlocal answer
            if not remaining:
                answer = min(answer, int(reverse) + swaps + sum(a != b for a, b in zip(current, second)))
                return
            a, *rest = remaining
            match(rest, current, swaps)
            for b in rest:
                following = current[:]
                following[a], following[b] = following[b], following[a]
                match([i for i in rest if i != b], following, swaps + 1)
        match(list(range(len(first))), initial, 0)
    return answer


def oracle3579(first, second):
    best = len(first)
    for cuts in range(1 << (len(first) - 1)):
        start, cost = 0, 0
        for end in range(1, len(first) + 1):
            if end == len(first) or cuts >> (end - 1) & 1:
                cost += oracle_segment(first[start:end], second[start:end])
                start = end
        best = min(best, cost)
    return best


def oracle3587(nums):
    initial = tuple(value % 2 for value in nums)
    queue, seen = deque([(initial, 0)]), {initial}
    while queue:
        current, distance = queue.popleft()
        if all(a != b for a, b in zip(current, current[1:])):
            return distance
        for i in range(len(current) - 1):
            following = list(current)
            following[i], following[i + 1] = following[i + 1], following[i]
            following = tuple(following)
            if following not in seen:
                seen.add(following)
                queue.append((following, distance + 1))
    return -1


def oracle3608(n, edges, k):
    for time in sorted({0} | {edge[2] for edge in edges}):
        adjacency = [[] for _ in range(n)]
        for a, b, removal in edges:
            if removal > time:
                adjacency[a].append(b)
                adjacency[b].append(a)
        seen, components = set(), 0
        for start in range(n):
            if start in seen:
                continue
            components += 1
            seen.add(start)
            stack = [start]
            while stack:
                for other in adjacency[stack.pop()]:
                    if other not in seen:
                        seen.add(other)
                        stack.append(other)
        if components >= k:
            return time


def public_examples():
    examples = {
        3217: [([[1,2,3],[1,2,3,4,5]], [4,5]), ([[1],[1,2,1,2,1,2]], [2,2,2]), ([[5],[1,2,3,4]], [1,2,3,4])],
        3231: [([[5,3,1,4,2]],3), ([[1,2,3,4,5]],1), ([[5,4,3,2,1]],5)],
        3237: [([[1,2,3],[3,3,2]],[2,3,1]), ([[1,4,2,3],[4,1,3]],[3,1,4,2])],
        3484: [([['Spreadsheet','getValue','setCell','getValue','setCell','getValue','resetCell','getValue'],[[3],['=5+7'],['A1',10],['=A1+6'],['B2',15],['=A1+B2'],['A1'],['=A1+B2']]],[None,12,None,16,None,25,None,15])],
        3517: [(['z'],'z'), (['babab'],'abbba'), (['daccad'],'acddca')],
        3524: [([[1,2,3,4,5],3],[9,2,4]), ([[1,2,4,8,16,32],4],[18,1,2,0]), ([[1,1,2,1,1],2],[9,6])],
        3531: [([3,[[1,2],[2,2],[3,2],[2,1],[2,3]]],1), ([3,[[1,1],[1,2],[2,1],[2,2]]],0), ([5,[[1,3],[3,2],[3,3],[3,5],[5,3]]],1)],
        3539: [([5,5,[1,10,100,10000,1000000]],991600007), ([2,2,[5,4,3,2,1]],170), ([1,1,[28]],28)],
        3551: [([[37,100]],1), ([[22,14,33,7]],0), ([[18,43,34,16]],2)],
        3559: [([[[1,2]],[[1,1],[1,2]]],[0,1]), ([[[1,2],[1,3],[3,4],[3,5]],[[1,4],[3,4],[2,5]]],[2,1,4])],
        3567: [([[[1,8],[3,-2]],2],[[2]]), ([[[3,-1]],1],[[0,0]]), ([[[1,-2,3],[2,3,5]],2],[[1,2]])],
        3574: [([[2,4],1],8), ([[3,5,7],2],14), ([[5,5,5],1],15)],
        3579: [(['abcdf','dacbe'],4), (['abceded','baecfef'],4), (['abcdef','fedabc'],2)],
        3587: [([[2,4,6,5,7]],3), ([[2,4,5,7]],1), ([[1,2,3]],0), ([[4,5,6,8]],-1)],
        3598: [([['jump','run','run','jump','run']],[3,0,0,3,3]), ([['dog','racer','car']],[0,0,0])],
        3608: [([2,[[0,1,3]],2],3), ([3,[[0,1,2],[1,2,4]],3],4), ([3,[[0,2,5]],2],0)],
        3618: [([[2,3,4]],1), ([[-1,5,7,0]],3)]
    }
    for pid, examples_for_id in examples.items():
        for args, expected in examples_for_id:
            add(pid, args, expected, 'public_example')


def random_cases():
    for _ in range(55):
        removed = RNG.sample(range(1,9), RNG.randint(1,6))
        values = [RNG.randint(1,9) for _ in range(RNG.randint(1,15))] + [9]
        add(3217,[removed,values],[x for x in values if x not in removed])
        nums = [RNG.randint(1,5) for _ in range(RNG.randint(1,8))]
        add(3231,[nums],oracle3231(nums))
        windows = RNG.sample(range(1,9),8)
        queries = [RNG.randint(1,8) for _ in range(RNG.randint(1,20))]
        expected=windows[:]
        for q in queries:
            expected.remove(q); expected.insert(0,q)
        add(3237,[windows,queries],expected)
        operations, arguments, expected = ['Spreadsheet'], [[4]], [None]
        grid=[[0]*26 for _ in range(4)]
        for _step in range(25):
            op=RNG.choice(['setCell','resetCell','getValue'])
            row,column=RNG.randrange(4),RNG.randrange(26)
            cell=chr(65+column)+str(row+1)
            operations.append(op)
            if op=='setCell':
                value=RNG.randint(0,100000); arguments.append([cell,value]); grid[row][column]=value; expected.append(None)
            elif op=='resetCell':
                arguments.append([cell]);grid[row][column]=0;expected.append(None)
            else:
                operands=[]; total=0
                for _term in range(2):
                    if RNG.randrange(2):
                        row,column=RNG.randrange(4),RNG.randrange(26)
                        operands.append(chr(65+column)+str(row+1));total+=grid[row][column]
                    else:
                        value=RNG.randint(0,100000);operands.append(str(value));total+=value
                arguments.append(['='+'+'.join(operands)]);expected.append(total)
        add(3484,[operations,arguments],expected)
        half=''.join(RNG.choice('abc') for _ in range(RNG.randint(0,3)))
        middle=RNG.choice('abc') if not half or RNG.randrange(2) else ''
        s=half+middle+half[::-1]
        expected=min(''.join(p) for p in set(permutations(s)) if p==p[::-1])
        add(3517,[s],expected)
        nums=[RNG.randint(1,1000000000) for _ in range(RNG.randint(1,10))];k=RNG.randint(1,5)
        expected=[0]*k
        for left in range(len(nums)):
            for right in range(left+1,len(nums)+1): expected[math.prod(nums[left:right])%k]+=1
        add(3524,[nums,k],expected)
        n=RNG.randint(2,6); buildings=RNG.sample(list(product(range(1,n+1),repeat=2)),RNG.randint(1,n*n))
        expected=sum(all(any((x==a and (y<b if direction==0 else y>b)) if direction<2 else
                            (y==b and (x<a if direction==2 else x>a)) for x,y in buildings)
                         for direction in range(4)) for a,b in buildings)
        add(3531,[n,buildings],expected)
        m=RNG.randint(1,5); k=RNG.randint(1,m); nums=[RNG.choice([1,2,7,99999999,100000000]) for _ in range(RNG.randint(1,4))]
        add(3539,[m,k,nums],oracle3539(m,k,nums))
        nums=RNG.sample(range(1,100),RNG.randint(1,5));add(3551,[nums],oracle3551(nums))
        n=RNG.randint(2,9); edges=[[v,RNG.randrange(1,v)] for v in range(2,n+1)]
        queries=[[RNG.randint(1,n),RNG.randint(1,n)] for _ in range(10)]
        add(3559,[edges,queries],oracle3559(edges,queries))
        rows,cols=RNG.randint(1,4),RNG.randint(1,4);k=RNG.randint(1,min(rows,cols))
        grid=[[RNG.randint(-5,5) for _ in range(cols)] for _ in range(rows)]
        expected=[]
        for top in range(rows-k+1):
            row=[]
            for left in range(cols-k+1):
                values=[grid[r][c] for r in range(top,top+k) for c in range(left,left+k)]
                row.append(min((abs(a-b) for a,b in combinations(values,2) if a!=b),default=0))
            expected.append(row)
        add(3567,[grid,k],expected)
        nums=[RNG.randint(1,30) for _ in range(RNG.randint(1,7))];k=RNG.randint(1,len(nums))
        add(3574,[nums,k],oracle3574(nums,k))
        n=RNG.randint(1,6); first=''.join(RNG.choice('abc') for _ in range(n));second=''.join(RNG.choice('abc') for _ in range(n))
        add(3579,[first,second],oracle3579(first,second))
        nums=RNG.sample(range(1,30),RNG.randint(1,8));add(3587,[nums],oracle3587(nums))
        words=[''.join(RNG.choice('abc') for _ in range(RNG.randint(1,6))) for _ in range(RNG.randint(1,10))]
        expected=[]
        for i in range(len(words)):
            remaining=words[:i]+words[i+1:];best=0
            for a,b in zip(remaining,remaining[1:]):
                length=0
                for x,y in zip(a,b):
                    if x!=y:break
                    length+=1
                best=max(best,length)
            expected.append(best)
        add(3598,[words],expected)
        n=RNG.randint(1,8);edges=[[a,b,RNG.randint(1,7)] for a,b in combinations(range(n),2) if RNG.randrange(3)==0];k=RNG.randint(1,n)
        add(3608,[n,edges,k],oracle3608(n,edges,k))
        nums=[RNG.randint(-1000000000,1000000000) for _ in range(RNG.randint(1,100))]
        def isprime(n):return n>=2 and all(n%d for d in range(2,math.isqrt(n)+1))
        add(3618,[nums],abs(sum(value if isprime(i) else -value for i,value in enumerate(nums))))


def structured_cases():
    add(3217,[[1],[1,2]*50000],[2]*50000,'large_shape')
    add(3231,[[7]*100000],100000,'large_shape')
    add(3237,[list(range(1,100001)),[50000]*100000],[50000]+list(range(1,50000))+list(range(50001,100001)),'large_shape')
    add(3517,['z'*100000],'z'*100000,'large_shape')
    add(3524,[[1000000000]*100000,1],[5000050000],'large_numeric')
    add(3539,[30,30,[1]*50],math.comb(50,30)*math.factorial(30)%MOD,'large_shape')
    add(3539,[30,4,[100000000]],pow(100000000,30,MOD),'large_numeric')
    n=100000
    add(3559,[[[i,i+1] for i in range(1,n)],[[1,n],[n,n],[50000,50001]]],[pow(2,n-2,MOD),0,1],'large_shape')
    add(3574,[[1000000000]*1500,1500],3000000000000,'large_numeric')
    add(3579,['a'*100,'b'*100],100,'large_shape')
    add(3587,[list(range(2,100002,2))+list(range(1,100001,2))],50000*49999//2,'large_numeric')
    add(3598,[['a']*100000],[1]*100000,'large_shape')
    add(3608,[100000,[[i,i+1,1000000000] for i in range(99999)],100000],1000000000,'large_shape')
    add(3618,[[1000000000]*100000],(100000-2*9592)*1000000000,'large_numeric')


def main():
    started=time.monotonic()
    public_examples(); random_cases(); structured_cases()
    modules={}
    syntax_checks=0
    for pid in IDS:
        path=ROOT/'python'/f'{pid}.py'
        compile(path.read_text(),str(path),'exec');syntax_checks+=1
        spec=importlib.util.spec_from_file_location(f'candidate_{pid}',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);modules[pid]=module
        subprocess.run(['node','--check',str(ROOT/'javascript'/f'{pid}.js')],check=True,capture_output=True,timeout=10);syntax_checks+=1
    for case in CASES:
        original=copy.deepcopy(case['args'])
        actual=modules[case['problem_id']].solve(*case['args'])
        assert actual==case['expected'],(case['problem_id'],case['category'],case['args'],actual,case['expected'])
        assert case['args']==original,(case['problem_id'],'input mutated')
    payload=[dict(problem_id=c['problem_id'],args=c['args']) for c in CASES]
    completed=subprocess.run(['node',str(HERE/'runner.js')],input=json.dumps(payload),text=True,capture_output=True,check=True,timeout=120)
    actuals=json.loads(completed.stdout)
    assert len(actuals)==len(CASES)
    for case,actual in zip(CASES,actuals):
        assert actual==case['expected'],(case['problem_id'],case['category'],case['args'],actual,case['expected'])
    # Native linked-list identity and rewiring, distinct from value-array adapter.
    module=modules[3217]; nodes=[module.ListNode(v) for v in [1,2,1,3,1]]
    for a,b in zip(nodes,nodes[1:]):a.next=b
    head=module.modifiedList([1],nodes[0])
    assert head is nodes[1] and head.next is nodes[3] and head.next.next is None
    # Native stateful API checked separately from operation tape.
    sheet=modules[3484].Spreadsheet(1000);sheet.setCell('Z1000',100000)
    assert sheet.getValue('=Z1000+100000')==200000
    sheet.resetCell('Z1000');assert sheet.getValue('=Z1000+A1')==0
    per_id={str(pid):dict(Counter(c['category'] for c in CASES if c['problem_id']==pid)) for pid in IDS}
    receipt=dict(schema='gamma.development-candidate-tests.v1',passed=True,seed=252002,
                 cases_per_language=len(CASES),language_assertions=2*len(CASES),syntax_checks=syntax_checks,
                 native_assertions_per_language=3,mutation_checks_per_language=len(CASES),per_id=per_id,
                 elapsed_seconds=round(time.monotonic()-started,3),python=platform.python_version(),
                 node=subprocess.check_output(['node','--version'],text=True).strip(),
                 qualification=False,protected_or_private_cases=False,
                 test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 runner_sha256=hashlib.sha256((HERE/'runner.js').read_bytes()).hexdigest(),
                 source_sha256={f'{lang}/{pid}.{suffix}':hashlib.sha256((ROOT/lang/f'{pid}.{suffix}').read_bytes()).hexdigest()
                                for pid in IDS for lang,suffix in [('python','py'),('javascript','js')]})
    (HERE/'test-results.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['source_sha256','per_id']},indent=2))


if __name__=='__main__':main()
