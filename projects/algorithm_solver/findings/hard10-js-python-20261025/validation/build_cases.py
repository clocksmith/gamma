"""Deterministic, self-authored local checks; no Gamma hidden tests are used.

Expected values are computed here, outside the candidate worker processes.
References intentionally use simpler methods than the candidate implementations.
"""
from __future__ import annotations
import itertools
import json
from functools import lru_cache
from pathlib import Path
import random
import re

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261025
rng = random.Random(SEED)
CASES = {int(p['id']): [] for p in json.loads((ROOT/'assignment.json').read_text())['problems']}


def add(pid, category, args, expected, note=''):
    CASES[pid].append({'case_id':f'{pid:04}-{len(CASES[pid])+1:06}',
                      'problem_id':pid,'category':category,'args':args,
                      'expected':expected,'note':note})


def rain_reference(values):
    return sum(min(max(values[:i+1]), max(values[i:])) - x
               for i,x in enumerate(values))


def histogram_reference(values):
    best = 0
    for left in range(len(values)):
        shortest = values[left]
        for right in range(left,len(values)):
            shortest = min(shortest,values[right])
            best = max(best,shortest*(right-left+1))
    return best


def prefix_table(matrix):
    rows, columns = len(matrix), len(matrix[0])
    table = [[0]*(columns+1) for _ in range(rows+1)]
    for row in range(rows):
        for column in range(columns):
            table[row+1][column+1] = (int(matrix[row][column])+table[row][column+1]
                                     +table[row+1][column]-table[row][column])
    return table


def rectangles(matrix):
    table = prefix_table(matrix)
    for top in range(len(matrix)):
        for bottom in range(top+1,len(matrix)+1):
            for left in range(len(matrix[0])):
                for right in range(left+1,len(matrix[0])+1):
                    yield ((bottom-top)*(right-left),
                           table[bottom][right]-table[top][right]
                           -table[bottom][left]+table[top][left])


def rectangle_reference(matrix):
    return max((area for area,total in rectangles(matrix) if area==total),default=0)


def stock_reference(prices):
    # Enumerate all single trades and every strictly ordered pair of trades.
    trades=[(buy,sell,prices[sell]-prices[buy])
            for buy in range(len(prices)) for sell in range(buy+1,len(prices))]
    best=max([0]+[profit for _,_,profit in trades])
    for _, first_sell, first_profit in trades:
        for second_buy, _, second_profit in trades:
            if first_sell < second_buy:
                best=max(best,first_profit+second_profit)
    return best


@lru_cache(maxsize=None)
def boxes_reference(boxes):
    # Exhaust every legal equal-color contiguous segment, including partial runs.
    best = 0
    for start in range(len(boxes)):
        end=start
        while end<len(boxes) and boxes[end]==boxes[start]:
            best=max(best,(end-start+1)**2+boxes_reference(boxes[:start]+boxes[end+1:]))
            end+=1
    return best


def palindrome_reference(text):
    # Independently binary-search the monotone ordered palindrome family at
    # every relevant length. Does not use the candidate's prefix +/- 1 rule.
    value=int(text)
    candidates={0}
    for length in range(max(1,len(text)-1),len(text)+2):
        half_length=(length+1)//2
        first=10**(half_length-1)
        end=10**half_length
        def palindrome(prefix):
            half=str(prefix)
            return int(half+(half[:-1] if length%2 else half)[::-1])
        low,high=first,end
        while low<high:
            middle=(low+high)//2
            if palindrome(middle)<value:
                low=middle+1
            else:
                high=middle
        for prefix in (low-1,low,low+1):
            if first<=prefix<end:
                candidate=palindrome(prefix)
                if candidate!=value:
                    candidates.add(candidate)
    candidates.discard(value)
    return str(min(candidates,key=lambda item:(abs(item-value),item)))


def palindrome_brute(value):
    distance=1
    while True:
        for candidate in (value-distance,value+distance):
            if candidate>=0 and str(candidate)==str(candidate)[::-1]:
                return str(candidate)
        distance+=1


def distinct_reference(values,k):
    answer=0
    for left in range(len(values)):
        seen=set()
        for right in range(left,len(values)):
            seen.add(values[right])
            if len(seen)==k:
                answer+=1
    return answer


def submatrices_reference(matrix,target):
    return sum(total==target for _,total in rectangles(matrix))


def increasing_reference(first,second):
    # Explore every allowed replacement at each position; no greedy choice,
    # frontier dominance pruning, or smallest-tail encoding.
    choices=tuple(set(second))
    @lru_cache(maxsize=None)
    def visit(index,previous):
        if index==len(first):
            return 0
        best=len(first)+1
        if first[index]>previous:
            best=visit(index+1,first[index])
        for replacement in choices:
            if replacement>previous:
                best=min(best,1+visit(index+1,replacement))
        return best
    answer=visit(0,-1)
    return answer if answer<=len(first) else -1


# Public examples: only input/output pairs, not copied statements or solutions.
examples={
10:[(['aa','a'],False),(['aa','a*'],True),(['ab','.*'],True)],
42:[([[0,1,0,2,1,0,1,3,2,1,2,1]],6),([[4,2,0,3,2,5]],9)],
84:[([[2,1,5,6,2,3]],10),([[2,4]],4)],
85:[([[list('10100'),list('10111'),list('11111'),list('10010')]],6),([[['0']]],0),([[['1']]],1)],
123:[([[3,3,5,0,0,3,1,4]],6),([[1,2,3,4,5]],4),([[7,6,4,3,1]],0)],
546:[([[1,3,2,2,2,3,4,3,1]],23),([[1,1,1]],9),([[1]],1)],
564:[(['123'],'121'),(['1'],'0')],
992:[([[1,2,1,2,3],2],7),([[1,2,1,3,4],3],3)],
1074:[([[[0,1,0],[1,1,1],[0,1,0]],0],4),([[[1,-1],[-1,1]],0],5),([[[904]],0],0)],
1187:[([[1,5,3,6,7],[1,3,2,4]],1),([[1,5,3,6,7],[4,3,1]],2),([[1,5,3,6,7],[1,6,3,3]],-1)],
}
for pid,rows in examples.items():
    for args,expected in rows:
        add(pid,'public_example',args,expected)

# 10: exhaustive small grammar, randomized valid patterns, and length limits.
patterns=[]
for count in range(1,4):
    patterns.extend(''.join(atoms) for atoms in itertools.product(('a','b','.','a*','b*','.*'),repeat=count))
strings=[''.join(chars) for size in range(1,5) for chars in itertools.product('ab',repeat=size)]
for pattern in patterns:
    matcher=re.compile(pattern)
    for string in strings:
        add(10,'exhaustive_oracle',[string,pattern],matcher.fullmatch(string) is not None)
for _ in range(400):
    string=''.join(rng.choice('abc') for _ in range(rng.randint(1,20)))
    pattern=''.join(rng.choice('abc.')+('*' if rng.random()<.45 else '') for _ in range(rng.randint(1,10)))
    add(10,'randomized_oracle',[string,pattern],re.fullmatch(pattern,string) is not None)
for args in [('a'*20,'a*'*10),('a'*19+'b','a*'*10),('ab'*10,'.*'*10),('a'*20,'a'*20),('mississippi','mis*is*p*.')]:
    add(10,'boundary',list(args),re.fullmatch(args[1],args[0]) is not None)
for args in [('',''),('','a*'),('','a'),('a',''),('','a*b*c*')]:
    add(10,'outside_domain_extension',list(args),re.fullmatch(args[1],args[0]) is not None,'Empty inputs are extensions, not normative coverage.')

# 42: per-column reference; reversal and translation metamorphic checks.
for size in range(1,7):
    for values in itertools.product(range(4),repeat=size):
        add(42,'exhaustive_oracle',[list(values)],rain_reference(values))
for _ in range(400):
    values=[rng.randrange(101) for _ in range(rng.randint(1,25))]
    expected=rain_reference(values)
    add(42,'randomized_oracle',[values],expected)
    if _<100:
        add(42,'metamorphic',[list(reversed(values))],expected,'Reverse the elevation map.')
        add(42,'metamorphic',[[x+100 for x in values]],expected,'Raise every bar equally.')
for values,expected in [([100000]+[0]*19998+[100000],1999800000),([100000]*20000,0),(list(range(20000)),0),(list(range(19999,-1,-1)),0)]:
    add(42,'analytic_stress',[values],expected)
add(42,'outside_domain_extension',[[]],0)

# 84: enumerate all intervals, including plateaus and zero heights.
for size in range(1,6):
    for values in itertools.product(range(5),repeat=size):
        add(84,'exhaustive_oracle',[list(values)],histogram_reference(values))
for _ in range(400):
    values=[rng.randrange(101) for _ in range(rng.randint(1,30))]
    answer=histogram_reference(values)
    add(84,'randomized_oracle',[values],answer)
    if _<100:
        add(84,'metamorphic',[list(reversed(values))],answer,'Reverse the histogram.')
for values,expected in [([10000]*100000,1000000000),([10000,0]*50000,10000),(list(range(1,10001)),25005000),([0]*100000,0)]:
    add(84,'analytic_stress',[values],expected)
add(84,'outside_domain_extension',[[]],0)

# 85: enumerate every rectangle using independent 2D sums.
for rows in range(1,4):
    for columns in range(1,4):
        for flat in itertools.product('01',repeat=rows*columns):
            matrix=[list(flat[i*columns:(i+1)*columns]) for i in range(rows)]
            add(85,'exhaustive_oracle',[matrix],rectangle_reference(matrix))
for _ in range(400):
    rows,columns=rng.randint(1,6),rng.randint(1,6)
    matrix=[[rng.choice('01') for _ in range(columns)] for _ in range(rows)]
    answer=rectangle_reference(matrix)
    add(85,'randomized_oracle',[matrix],answer)
    if _<100:
        add(85,'metamorphic',[[list(row) for row in zip(*matrix)]],answer,'Transpose the matrix.')
for matrix,expected in [([['1']*200 for _ in range(200)],40000),([['0']*200 for _ in range(200)],0),([[str((r+c)%2) for c in range(200)] for r in range(200)],1),([['1']*200],200)]:
    add(85,'analytic_stress',[matrix],expected)
for matrix in ([],[[]]):
    add(85,'outside_domain_extension',[matrix],0)

# 123: all transaction schedules on small price series.
for size in range(1,7):
    for values in itertools.product(range(4),repeat=size):
        add(123,'exhaustive_oracle',[list(values)],stock_reference(values))
for _ in range(400):
    values=[rng.randrange(100001) for _ in range(rng.randint(1,12))]
    add(123,'randomized_oracle',[values],stock_reference(values))
for values,expected in [([0,100000]*50000,200000),(list(range(1,100001)),99999),([100000]*100000,0),(list(range(100000,0,-1)),0)]:
    add(123,'analytic_stress',[values],expected)
add(123,'outside_domain_extension',[[]],0)

# 546: all legal removals, not the candidate's interval recurrence.
for size in range(1,8):
    for values in itertools.product((1,2,3),repeat=size):
        add(546,'exhaustive_oracle',[list(values)],boxes_reference(values))
for _ in range(150):
    values=tuple(rng.randint(1,5) for _ in range(rng.randint(1,9)))
    answer=boxes_reference(values)
    add(546,'randomized_oracle',[list(values)],answer)
    if _<50:
        add(546,'metamorphic',[[x+40 for x in values]],answer,'One-to-one renaming of colors.')
for values,expected in [([1]*100,10000),(list(range(1,101)),100),([1]*40+[2]*20+[1]*40,6800),([1]*30+[2]*40+[1]*30,5200)]:
    add(546,'analytic_stress',[values],expected)
add(546,'outside_domain_extension',[[]],0)

# 564: brute distance enumeration for small values; separate monotone-family
# reference for large values. Cross-check the latter's implementation on the small set.
for value in range(1,5001):
    expected=palindrome_brute(value)
    assert palindrome_reference(str(value))==expected,('palindrome oracle disagreement',value)
    add(564,'exhaustive_oracle',[str(value)],expected)
for _ in range(1000):
    length=rng.randint(1,18)
    value=rng.randrange(10**(length-1),10**length)
    add(564,'randomized_oracle',[str(value)],palindrome_reference(str(value)))
for digits in range(1,19):
    for value in (10**(digits-1),10**(digits-1)+1,10**digits-2,10**digits-1):
        if 1<=value<10**18:
            add(564,'boundary',[str(value)],palindrome_reference(str(value)))
for value in (2**53-1,2**53,2**53+1,999999999999999999,100000000000000001,100000000000000000):
    add(564,'boundary',[str(value)],palindrome_reference(str(value)),'Exact arithmetic beyond JavaScript safe-integer range.')

# 992: all intervals and set cardinalities.
for size in range(1,7):
    for values in itertools.product(range(1,min(3,size)+1),repeat=size):
        for k in range(1,size+1):
            add(992,'exhaustive_oracle',[list(values),k],distinct_reference(values,k))
for _ in range(400):
    size=rng.randint(1,25)
    values=[rng.randint(1,size) for _ in range(size)]
    k=rng.randint(1,size)
    add(992,'randomized_oracle',[values,k],distinct_reference(values,k))
for args,expected in [([[1]*20000,1],200010000),([[1]*20000,2],0),([list(range(1,20001)),20000],1),([list(range(1,20001)),1],20000),([[1,2]*10000,2],199990000)]:
    add(992,'analytic_stress',args,expected)
add(992,'outside_domain_extension',[[],1],0)
add(992,'outside_domain_extension',[[1,1],0],0)

# 1074: enumerate all rectangles with 2D sums.
for rows,columns in ((1,1),(1,2),(2,1),(2,2),(2,3)):
    for flat in itertools.product((-1,0,1),repeat=rows*columns):
        matrix=[list(flat[i*columns:(i+1)*columns]) for i in range(rows)]
        for target in (-1,0,1):
            add(1074,'exhaustive_oracle',[matrix,target],submatrices_reference(matrix,target))
for _ in range(400):
    rows,columns=rng.randint(1,5),rng.randint(1,5)
    matrix=[[rng.randint(-8,8) for _ in range(columns)] for _ in range(rows)]
    target=rng.randint(-25,25)
    answer=submatrices_reference(matrix,target)
    add(1074,'randomized_oracle',[matrix,target],answer)
    if _<100:
        add(1074,'metamorphic',[[list(row) for row in zip(*matrix)],target],answer,'Transpose preserves rectangle counts.')
for args,expected in [([[[0]*100 for _ in range(100)],0],25502500),([[[1]*100 for _ in range(100)],1],10000),([[[-1000]*100 for _ in range(100)],-10000000],1),([[[0]*100],0],5050),([[[0] for _ in range(100)],0],5050),([[[1000]*100 for _ in range(100)],100000000],0)]:
    add(1074,'analytic_stress',args,expected)
add(1074,'outside_domain_extension',[[],0],0)

# 1187: every replacement choice on small domains, then full-size closed forms.
subsets=[list(values) for size in range(1,5) for values in itertools.combinations(range(4),size)]
for size in range(1,5):
    for first in itertools.product(range(4),repeat=size):
        for second in subsets:
            add(1187,'exhaustive_oracle',[list(first),second],increasing_reference(first,second))
for _ in range(400):
    first=[rng.randrange(11) for _ in range(rng.randint(1,7))]
    second=[rng.randrange(11) for _ in range(rng.randint(1,6))]
    answer=increasing_reference(first,second)
    add(1187,'randomized_oracle',[first,second],answer)
    if _<100:
        add(1187,'metamorphic',[[x+100 for x in first],[x+100 for x in second]],answer,'Translate both input value sets equally.')
for args,expected in [([list(range(2000)),[1000000000]],0),([list(range(2000,0,-1)),list(range(1,2001))],2000),([list(range(1999,0,-1)),list(range(1,2000))],1998),([[0]*2000,list(range(1,2001))],1999),([[1000000000]*2000,[0]],-1),([[1000000000],[1000000000]],0)]:
    add(1187,'analytic_stress',args,expected)
add(1187,'outside_domain_extension',[[],[1]],0)


def check_domain(pid,args):
    def ints(values,low,high,limit):
        return 1<=len(values)<=limit and all(type(v) is int and low<=v<=high for v in values)
    if pid==10:
        s,p=args
        return 1<=len(s)<=20 and 1<=len(p)<=20 and re.fullmatch('[a-z]+',s) is not None and re.fullmatch(r'(?:[a-z.]\*?)+',p) is not None
    if pid==42: return ints(args[0],0,100000,20000)
    if pid==84: return ints(args[0],0,10000,100000)
    if pid==85:
        matrix=args[0]
        return 1<=len(matrix)<=200 and 1<=len(matrix[0])<=200 and all(len(row)==len(matrix[0]) and all(type(x) is str and x in ('0','1') for x in row) for row in matrix)
    if pid==123: return ints(args[0],0,100000,100000)
    if pid==546: return ints(args[0],1,100,100)
    if pid==564: return re.fullmatch('[1-9][0-9]{0,17}',args[0]) is not None
    if pid==992: return ints(args[0],1,len(args[0]),20000) and 1<=args[1]<=len(args[0])
    if pid==1074:
        matrix,target=args
        return 1<=len(matrix)<=100 and 1<=len(matrix[0])<=100 and all(len(row)==len(matrix[0]) and ints(row,-1000,1000,100) for row in matrix) and -100000000<=target<=100000000
    if pid==1187: return ints(args[0],0,1000000000,2000) and ints(args[1],0,1000000000,2000)
    return False

out=ROOT/'validation'/'cases'
out.mkdir(exist_ok=True)
for pid,rows in CASES.items():
    for row in rows:
        if row['category']!='outside_domain_extension':
            assert check_domain(pid,row['args']),('invalid normative test input',pid,row['case_id'])
    (out/f'{pid:04}.jsonl').write_text(''.join(json.dumps(row,separators=(',',':'))+'\n' for row in rows))
    print(pid,len(rows))
print('TOTAL',sum(map(len,CASES.values())))
