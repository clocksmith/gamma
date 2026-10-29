"""Independent bounded reference algorithms; no candidate imports."""
from collections import Counter,deque
from decimal import Decimal,localcontext
from fractions import Fraction
from functools import lru_cache
from itertools import combinations,groupby,permutations
from math import ceil,exp,isfinite
import re
IDS=(770,782,799,803,805,808,817,818)
NATIVE=(817,)
FLOAT_TOLERANCE={799:1e-5,808:1e-5}
INT32=(-2**31,2**31-1)
def integer(v,lo,hi):
    if type(v) is not int or not lo<=v<=hi:raise ValueError('integer domain')
def array(a,lo,hi,minimum=1,maximum=100000):
    if type(a) is not list or not minimum<=len(a)<=maximum:raise ValueError('array size')
    for v in a:integer(v,lo,hi)
def word(w,minimum,maximum):
    if type(w) is not str or not minimum<=len(w)<=maximum or not re.fullmatch('[a-z]+',w):raise ValueError('word domain')
CHUNK=re.compile(r'(\(*)([a-z]+|[0-9]+)(\)*)')
def expression_tokens(s):
    """Grammar check for the 770 expression: single-space separated symbols and chunks; returns token list."""
    if type(s) is not str or not 1<=len(s)<=250 or set(s)-set('abcdefghijklmnopqrstuvwxyz0123456789+-*() '):raise ValueError('expression characters')
    tokens=[];depth=0
    for position,part in enumerate(s.split(' ')):
        if position%2:
            if part not in ('+','-','*'):raise ValueError('expression symbol')
            tokens.append(part);continue
        match=CHUNK.fullmatch(part)
        if not match:raise ValueError('expression chunk')
        tokens += list(match.group(1));tokens.append(match.group(2))
        depth += len(match.group(1))
        for _ in match.group(3):
            depth -= 1
            if depth<0:raise ValueError('parenthesis balance')
            tokens.append(')')
    if depth or s.split(' ')[-1] in ('+','-','*') or len(s.split(' '))%2==0:raise ValueError('expression structure')
    return tokens
def validate_domain(pid,args):
    arity={770:3,782:1,799:3,803:2,805:1,808:1,817:2,818:1}
    if pid not in arity or type(args) is not list or len(args)!=arity[pid]:raise ValueError('argument envelope')
    if pid==770:
        expression_tokens(args[0]);names,values=args[1],args[2]
        if type(names) is not list or not 0<=len(names)<=100:raise ValueError('evalvars size')
        for w in names:word(w,1,20)
        array(values,-100,100,0,100)
        if len(values)!=len(names):raise ValueError('evalints length')
        polynomial_reference(args[0],names,values)
    if pid==782:
        board=args[0]
        if type(board) is not list or not 2<=len(board)<=30:raise ValueError('board size')
        for row in board:array(row,0,1,len(board),len(board))
    if pid==799:integer(args[0],0,10**9);integer(args[1],0,99);integer(args[2],0,args[1])
    if pid==803:
        grid,hits=args
        if type(grid) is not list or not 1<=len(grid)<=200:raise ValueError('grid rows')
        for row in grid:array(row,0,1,1,200)
        if len({len(row) for row in grid})!=1:raise ValueError('grid width')
        if type(hits) is not list or not 1<=len(hits)<=40000:raise ValueError('hits size')
        for hit in hits:
            if type(hit) is not list or len(hit)!=2:raise ValueError('hit pair')
            integer(hit[0],0,len(grid)-1);integer(hit[1],0,len(grid[0])-1)
        if len({tuple(hit) for hit in hits})!=len(hits):raise ValueError('hit uniqueness')
    if pid==805:array(args[0],0,10**4,1,30)
    if pid==808:integer(args[0],0,10**9)
    if pid==817:
        packet,nums=args
        if type(packet) is not dict or set(packet)!={'values'} or type(packet['values']) is not list:raise ValueError('indexed native packet')
        values=packet['values'];n=len(values)
        array(values,0,max(n-1,0),1,10**4)
        if len(set(values))!=n:raise ValueError('node value uniqueness')
        array(nums,0,n-1,1,n)
        if len(set(nums))!=len(nums) or set(nums)-set(values):raise ValueError('nums subset uniqueness')
    if pid==818:integer(args[0],1,10**4)
def compare(pid,actual,expected):
    if pid in FLOAT_TOLERANCE:
        return type(actual) in (int,float) and type(actual) is not bool and isfinite(actual) and abs(actual-expected)<=FLOAT_TOLERANCE[pid]
    return type(actual) is type(expected) and actual==expected
def polynomial_reference(expression,names,values):
    """Shunting-yard to postfix, then Counter polynomials keyed by sorted variable tuples."""
    env=dict(zip(names,values));output=[];operators=[];rank={'+':1,'-':1,'*':2}
    for token in expression_tokens(expression):
        if token=='(':operators.append(token)
        elif token==')':
            while operators[-1]!='(':output.append(operators.pop())
            operators.pop()
        elif token in rank:
            while operators and operators[-1]!='(' and rank[operators[-1]]>=rank[token]:output.append(operators.pop())
            operators.append(token)
        else:output.append(token)
    output += reversed(operators)
    def checked(poly):
        poly=Counter({k:v for k,v in poly.items() if v})
        if any(not INT32[0]<=v<=INT32[1] for v in poly.values()):raise ValueError('intermediate domain')
        return poly
    stack=[]
    for token in output:
        if token.isdigit():stack.append(checked(Counter({():int(token)})))
        elif token.isalpha():stack.append(checked(Counter({():env[token]}) if token in env else Counter({(token,):1})))
        else:
            right=stack.pop();left=stack.pop();result=Counter()
            if token=='*':
                for a,x in left.items():
                    for b,y in right.items():result[tuple(sorted(a+b))]+=x*y
            else:
                result.update(left)
                for b,y in right.items():result[b]+=y if token=='+' else -y
            stack.append(checked(result))
    (poly,)=stack
    return [str(v)+''.join('*'+name for name in k) for k,v in sorted(poly.items(),key=lambda item:(-len(item[0]),item[0]))]
def chessboard_reference(board):
    """All row permutations x column permutations; swaps = n - cycle count per permutation."""
    n=len(board)
    if n>5:raise ValueError('reference budget')
    def swaps(p):
        seen=set();cycles=0
        for i in range(n):
            if i not in seen:
                cycles+=1;j=i
                while j not in seen:seen.add(j);j=p[j]
        return n-cycles
    perms=list(permutations(range(n)));best=None
    for rows in perms:
        moved=[board[r] for r in rows]
        for cols in perms:
            first=moved[0][cols[0]]
            if all(moved[i][cols[j]]==first^((i+j)&1) for i in range(n) for j in range(n)):
                cost=swaps(rows)+swaps(cols)
                if best is None or cost<best:best=cost
    return -1 if best is None else best
def champagne_reference(poured,row,glass):
    """Exact rational top-down inflow per glass."""
    @lru_cache(None)
    def inflow(r,c):
        if r==0:return Fraction(poured)
        total=Fraction(0)
        for pr,pc in ((r-1,c-1),(r-1,c)):
            if 0<=pc<=pr:total+=max(Fraction(0),inflow(pr,pc)-1)/2
        return total
    return float(min(Fraction(1),inflow(row,glass)))
def bricks_reference(grid,hits):
    """Literal simulation: erase, then flood from the top row and drop every unreached brick.
    Interpretation: bricks already unstable in the initial grid are removed before the first hit and never counted."""
    m,n=len(grid),len(grid[0])
    if len(hits)*m*n>3*10**6:raise ValueError('reference budget')
    def stable_part(cells):
        stable={cell for cell in cells if cell[0]==0};pending=deque(stable)
        while pending:
            r0,c0=pending.popleft()
            for cell in ((r0+1,c0),(r0-1,c0),(r0,c0+1),(r0,c0-1)):
                if cell in cells and cell not in stable:stable.add(cell);pending.append(cell)
        return stable
    cells=stable_part({(r,c) for r in range(m) for c in range(n) if grid[r][c]==1});answer=[]
    for r,c in hits:
        if (r,c) not in cells:answer.append(0);continue
        cells.discard((r,c));stable=stable_part(cells)
        answer.append(len(cells)-len(stable));cells=stable
    return answer
def average_split_reference(nums):
    """Small n: every proper nonempty subset with exact Fraction averages. Otherwise per-size sum bitsets."""
    n=len(nums);total=sum(nums)
    if n<=12:
        whole=Fraction(total,n)
        return any(Fraction(sum(c),k)==whole for k in range(1,n) for c in combinations(nums,k))
    reach=[0]*(n+1);reach[0]=1
    for x in nums:
        for k in range(n,0,-1):reach[k]|=reach[k-1]<<x
    return any(total*k%n==0 and reach[k]>>(total*k//n)&1 for k in range(1,n))
SOUP_TABLE_UNITS=1000
@lru_cache(None)
def soup_table():
    """High-precision Decimal bottom-up table over 25 mL units; independent of float arithmetic."""
    size=SOUP_TABLE_UNITS;half=Decimal('0.5');quarter=Decimal('0.25');rows=[]
    with localcontext() as ctx:
        ctx.prec=45
        def value(a,b):
            if a<=0 and b<=0:return half
            if a<=0:return Decimal(1)
            if b<=0:return Decimal(0)
            return rows[a][b]
        for a in range(size+1):
            row=[]
            rows.append(row)
            for b in range(size+1):
                if a==0 or b==0:row.append(None);continue
                row.append((value(a-4,b)+value(a-3,b-1)+value(a-2,b-2)+value(a-1,b-3))*quarter)
        return tuple(half if m==0 else rows[m][m] for m in range(size+1))
def soup_hoeffding_tail(units):
    """Bound on P(B empty no later than A): needs D(t)=A-B poured units<4 at some t>=units/3; steps in [-2,4], mean 1."""
    start=ceil(units/3)
    if start<=8:raise ValueError('certificate range')
    # For t>=9 consecutive terms shrink by at least exp(-0.82/18)<0.956, so the tail after a term is below 23*term.
    total=0.0;t=start
    while True:
        term=exp(-2*(t-4)**2/(36*t))
        if term<1e-40:return total+23*term
        total+=term;t+=1
def soup_reference(n):
    units=-(-n//25)
    if units<=SOUP_TABLE_UNITS:return float(soup_table()[units])
    if soup_hoeffding_tail(units)>1e-6:raise ValueError('certificate budget')
    return 1.0
def soup_exact_ml(n):
    """Exact Fraction recursion directly on millilitres for small n (test cross-check only)."""
    if n>1500:raise ValueError('reference budget')
    @lru_cache(None)
    def f(a,b):
        if a<=0 and b<=0:return Fraction(1,2)
        if a<=0:return Fraction(1)
        if b<=0:return Fraction(0)
        return sum((f(a-x,b-y) for x,y in ((100,0),(75,25),(50,50),(25,75))),Fraction(0))/4
    return f(n,n)
def components_reference(values,nums):
    member=set(nums)
    return sum(key for key,_ in groupby(v in member for v in values))
RACE_LIMIT=10**4
@lru_cache(None)
def race_distances():
    """BFS over (position,speed) with loose bounds; first distance per position. Bound is wider than the common 2*target prune, not proved."""
    low,high,speed_cap=-2*RACE_LIMIT-2,4*RACE_LIMIT+4,2**16
    best={0:0};seen={(0,1)};pending=deque([(0,1,0)])
    while pending:
        position,speed,cost=pending.popleft()
        for state in ((position+speed,speed*2),(position,-1 if speed>0 else 1)):
            if state in seen or not low<=state[0]<=high or abs(state[1])>speed_cap:continue
            seen.add(state);pending.append((state[0],state[1],cost+1))
            if state[0] not in best:best[state[0]]=cost+1
    return best
def reference(pid,args):
    validate_domain(pid,args)
    if pid==770:return polynomial_reference(*args)
    if pid==782:return chessboard_reference(args[0])
    if pid==799:return champagne_reference(*args)
    if pid==803:return bricks_reference(*args)
    if pid==805:return average_split_reference(args[0])
    if pid==808:return soup_reference(args[0])
    if pid==817:return components_reference(args[0]['values'],args[1])
    if pid==818:return race_distances()[args[0]]
