"""Independent bounded reference algorithms and official-domain validators; no candidate imports."""
from collections import Counter
from itertools import combinations
import re
IDS=(726,729,730,731,732,736,741)
CLASSES={729:'MyCalendar',731:'MyCalendarTwo',732:'MyCalendarThree'}
BOOK_LIMIT={729:1000,731:1000,732:400}
INT32=(-2**31,2**31-1)
def integer(v,lo,hi):
    if type(v) is not int or not lo<=v<=hi:raise ValueError('integer domain')
def formula_counts(formula):
    """Iterative grammar check: element counts >=2, group counts >=1, no empty group, no leading zero."""
    if type(formula) is not str or not 1<=len(formula)<=1000 or re.fullmatch(r'[A-Za-z0-9()]+',formula) is None:raise ValueError('formula alphabet/length')
    stack=[[Counter(),False]];i=0;n=len(formula)
    def number(i):
        j=i
        while j<n and formula[j].isdigit():j+=1
        if j==i:return 1,i
        if formula[i]=='0':raise ValueError('count leading zero')
        return int(formula[i:j]),j
    while i<n:
        c=formula[i]
        if c=='(':stack.append([Counter(),False]);i+=1
        elif c==')':
            if len(stack)==1 or not stack[-1][1]:raise ValueError('unbalanced or empty group')
            inner=stack.pop()[0];k,i=number(i+1)
            for name,v in inner.items():stack[-1][0][name]+=v*k
            stack[-1][1]=True
        elif 'A'<=c<='Z':
            j=i+1
            while j<n and 'a'<=formula[j]<='z':j+=1
            name=formula[i:j];k,i=number(j)
            if i!=j and k<2:raise ValueError('explicit element count must exceed one')
            stack[-1][0][name]+=k;stack[-1][1]=True
        else:raise ValueError('unit must start with element or group')
    if len(stack)!=1 or not stack[0][1]:raise ValueError('unbalanced formula')
    if max(stack[0][0].values())>INT32[1]:raise ValueError('output count exceeds 32-bit')
    return stack[0][0]
TOKEN=re.compile(r'\(|\)|[^ ()]+')
KEYWORDS=('add','let','mult')
def lisp_tree(expression):
    if type(expression) is not str or not 1<=len(expression)<=2000:raise ValueError('expression length')
    tokens=TOKEN.findall(expression);pos=0
    def parse():
        nonlocal pos
        if pos>=len(tokens):raise ValueError('truncated')
        t=tokens[pos];pos+=1
        if t==')':raise ValueError('unexpected close')
        if t!='(':return t
        items=[]
        while pos<len(tokens) and tokens[pos]!=')':items.append(parse())
        if pos>=len(tokens):raise ValueError('unclosed')
        pos+=1;return items
    tree=parse()
    if pos!=len(tokens):raise ValueError('trailing tokens')
    def render(x):return x if type(x) is str else '('+' '.join(map(render,x))+')'
    if render(tree)!=expression:raise ValueError('single-space token format required')
    return tree
def is_variable(t):return type(t) is str and re.fullmatch(r'[a-z][a-z0-9]*',t) is not None and t not in KEYWORDS
def lisp_value(tree,env):
    """Persistent-dictionary scopes: each let evaluates in a fresh copy of its enclosing scope."""
    if type(tree) is str:
        if re.fullmatch(r'-?[0-9]+',tree):value=int(tree)
        elif is_variable(tree):
            if tree not in env:raise ValueError('unbound variable')
            value=env[tree]
        else:raise ValueError('bad atom')
    else:
        if not tree or tree[0] not in KEYWORDS:raise ValueError('bad operator')
        op=tree[0]
        if op in ('add','mult'):
            if len(tree)!=3:raise ValueError('binary arity')
            a,b=lisp_value(tree[1],env),lisp_value(tree[2],env);value=a+b if op=='add' else a*b
        else:
            if len(tree)<4 or len(tree)%2:raise ValueError('let arity')
            scope=dict(env)
            for k in range(1,len(tree)-1,2):
                if not is_variable(tree[k]):raise ValueError('let variable')
                scope=dict(scope);scope[tree[k]]=lisp_value(tree[k+1],scope)
            value=lisp_value(tree[-1],scope)
    if not INT32[0]<=value<=INT32[1]:raise ValueError('32-bit intermediate')
    return value
def validate_domain(pid,args):
    arity={726:1,729:2,730:1,731:2,732:2,736:1,741:1}
    if pid not in arity or type(args) is not list or len(args)!=arity[pid]:raise ValueError('argument envelope')
    if pid==726:formula_counts(args[0])
    if pid in CLASSES:
        ops,rows=args
        if type(ops) is not list or type(rows) is not list or not ops or len(ops)!=len(rows):raise ValueError('parallel trace lists')
        if type(ops[0]) is not str or ops[0]!=CLASSES[pid] or type(rows[0]) is not list or rows[0]!=[]:raise ValueError('one initial empty constructor')
        if len(ops)-1>BOOK_LIMIT[pid]:raise ValueError('book call limit')
        for op,row in zip(ops[1:],rows[1:]):
            if type(op) is not str or op!='book' or type(row) is not list or len(row)!=2:raise ValueError('book(startTime,endTime) only')
            integer(row[0],0,10**9-1);integer(row[1],row[0]+1,10**9)
    if pid==730:
        s=args[0]
        if type(s) is not str or not 1<=len(s)<=1000 or set(s)-set('abcd'):raise ValueError('string domain')
    if pid==736:lisp_value(lisp_tree(args[0]),{})
    if pid==741:
        grid=args[0]
        if type(grid) is not list or not 1<=len(grid)<=50:raise ValueError('grid size')
        for row in grid:
            if type(row) is not list or len(row)!=len(grid):raise ValueError('square grid')
            for v in row:
                if type(v) is not int or v not in (-1,0,1):raise ValueError('cell domain')
        if grid[0][0]==-1 or grid[-1][-1]==-1:raise ValueError('corner thorn')
def formula_tree(formula):
    pos=0
    def count():
        nonlocal pos
        j=pos
        while j<len(formula) and formula[j].isdigit():j+=1
        k=int(formula[pos:j]) if j>pos else 1;pos=j;return k
    def sequence():
        nonlocal pos
        nodes=[]
        while pos<len(formula) and formula[pos]!=')':
            if formula[pos]=='(':
                pos+=1;inner=sequence();pos+=1;nodes.append(('group',inner,count()))
            else:
                j=pos+1
                while j<len(formula) and formula[j].islower():j+=1
                name=formula[pos:j];pos=j;nodes.append(('atom',name,count()))
        return nodes
    return sequence()
def reference(pid,args):
    validate_domain(pid,args)
    if pid==726:
        formula=args[0]
        if len(formula)>200:raise ValueError('reference budget')
        budget=[200000]
        def expand(nodes):
            out=[]
            for kind,body,k in nodes:
                one=[body] if kind=='atom' else expand(body)
                budget[0]-=len(one)*k
                if budget[0]<0:raise ValueError('reference expansion budget')
                out.extend(one*k)
            return out
        atoms=Counter(expand(formula_tree(formula)))
        return ''.join(name+(str(atoms[name]) if atoms[name]>1 else '') for name in sorted(atoms))
    if pid==729:
        accepted=[];out=[None]
        for s,e in args[1][1:]:
            ok=all(max(s,a)>=min(e,b) for a,b in accepted)
            if ok:accepted.append((s,e))
            out.append(ok)
        return out
    if pid==731:
        if len(args[0])>201:raise ValueError('reference budget')
        accepted=[];out=[None]
        for s,e in args[1][1:]:
            points={s}|{a for a,b in accepted if s<=a<e}
            ok=all(sum(a<=p<b for a,b in accepted)<2 for p in points)
            if ok:accepted.append((s,e))
            out.append(ok)
        return out
    if pid==732:
        if len(args[0])>121:raise ValueError('reference budget')
        accepted=[];out=[None]
        for s,e in args[1][1:]:
            accepted.append((s,e))
            out.append(max(sum(a<=p<b for a,b in accepted) for p,_ in accepted))
        return out
    if pid==730:
        s=args[0]
        if len(s)<=12:
            found=set()
            for mask in range(1,1<<len(s)):
                t=''.join(s[i] for i in range(len(s)) if mask>>i&1)
                if t==t[::-1]:found.add(t)
            return len(found)%(10**9+7)
        return palindrome_letter_intervals(s)
    if pid==736:
        if len(args[0])>2000:raise ValueError('reference budget')
        return lisp_value(lisp_tree(args[0]),{})
    if pid==741:
        grid=args[0];n=len(grid)
        if n>6:raise ValueError('reference budget')
        paths=[]
        for downs in combinations(range(2*n-2),n-1):
            r=c=0;cells=[(0,0)]
            for step in range(2*n-2):
                if step in downs:r+=1
                else:c+=1
                cells.append((r,c))
            if all(grid[a][b]!=-1 for a,b in cells):paths.append(set(cells))
        return max((sum(grid[a][b] for a,b in p|q) for p in paths for q in paths),default=0)
def palindrome_letter_intervals(s):
    """Classify distinct palindromes of s[i..j] by outer letter: outermost pair plus distinct inner palindromes."""
    n=len(s);modulus=10**9+7
    if n>300:raise ValueError('reference budget')
    first=[[n]*4 for _ in range(n+1)];last=[[-1]*4 for _ in range(n+1)]
    for i in range(n-1,-1,-1):
        first[i]=first[i+1][:];first[i]['abcd'.index(s[i])]=i
    for i in range(n):
        last[i+1]=last[i][:];last[i+1]['abcd'.index(s[i])]=i
    f=[[0]*(n+1) for _ in range(n+1)]
    for length in range(1,n+1):
        for i in range(0,n-length+1):
            j=i+length-1;total=0
            for c in range(4):
                lo,hi=first[i][c],last[j+1][c]
                if lo>j:continue
                total+=1 if lo==hi else 2+(f[lo+1][hi-1] if lo+1<=hi-1 else 0)
            f[i][j]=total%modulus
    return f[0][n-1]
