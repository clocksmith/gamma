"""Independent small-domain references; no candidate imports or result agreement oracle."""
from collections import deque
from itertools import product
class TreeNode:
    def __init__(self,val=0,left=None,right=None):self.val,self.left,self.right=val,left,right

def build(values):
    nodes=[TreeNode(v) for v in values]
    for i,node in enumerate(nodes):
        if 2*i+1<len(nodes):node.left=nodes[2*i+1]
        if 2*i+2<len(nodes):node.right=nodes[2*i+2]
    return nodes[0]

def snapshot(root):
    q=deque([root]);out=[]
    while q:
        node=q.popleft()
        if node is None:out.append(None);continue
        out.append(node.val);q.append(node.left);q.append(node.right)
    while out and out[-1] is None:out.pop()
    return out

def domain(pid,args):
    def integer(x,a,b):assert type(x) is int and a<=x<=b
    if pid==912:
        nums,=args;integer(len(nums),1,50000)
        for x in nums:integer(x,-50000,50000)
    elif pid==919:
        ops,rows=args;assert ops[0]=='CBTInserter' and len(rows[0])==1;values=rows[0][0];integer(len(values),1,1000)
        for x in values:integer(x,0,5000)
        integer(len(ops)-1,0,10000);assert len(ops)==len(rows)
        for op,row in zip(ops[1:],rows[1:]):
            if op=='insert':assert len(row)==1;integer(row[0],0,5000)
            else:assert op=='get_root' and row==[]
    elif pid==924:
        g,initial=args;n=len(g);integer(n,2,300);assert len(initial)==len(set(initial)) and 1<=len(initial)<=n
        for i,row in enumerate(g):
            assert len(row)==n and row[i]==1
            for j,x in enumerate(row):integer(x,0,1);assert x==g[j][i]
        for x in initial:integer(x,0,n-1)
    elif pid==933:
        ops,rows=args;assert ops[0]=='RecentCounter' and rows[0]==[] and len(ops)==len(rows);integer(len(ops)-1,0,10000);last=0
        for op,row in zip(ops[1:],rows[1:]):assert op=='ping' and len(row)==1;integer(row[0],last+1,10**9);last=row[0]
    elif pid==943:
        words,=args;integer(len(words),1,12);assert len(words)==len(set(words))
        for i,s in enumerate(words):assert 1<=len(s)<=20 and all('a'<=ch<='z' for ch in s);assert all(i==j or s not in t for j,t in enumerate(words))
    elif pid==959:
        grid,=args;n=len(grid);integer(n,1,30);assert all(len(row)==n and set(row)<=set('/\\ ') for row in grid)
    else:raise ValueError(pid)

def reference(pid,args):
    domain(pid,args)
    if pid==912:return sorted(args[0])
    if pid==919:
        operations,rows=args;root=build(rows[0][0]);out=[None]
        for op,row in zip(operations[1:],rows[1:]):
            if op=='get_root':out.append(snapshot(root));continue
            # Literal BFS from scratch for the first empty child slot, independent of candidate indexing.
            q=deque([root])
            while q:
                node=q.popleft()
                if node.left is None:node.left=TreeNode(row[0]);out.append(node.val);break
                if node.right is None:node.right=TreeNode(row[0]);out.append(node.val);break
                q.extend([node.left,node.right])
        return out
    if pid==924:
        g,initial=args;n=len(g);options=[]
        for removed in initial:
            infected=set(initial)-{removed};changed=True
            while changed:
                nxt=infected|{v for u in infected for v in range(n) if g[u][v]}
                changed=nxt!=infected;infected=nxt
            options.append((len(infected),removed))
        return min(options)[1]
    if pid==933:
        operations,rows=args;history=[];out=[None]
        for row in rows[1:]:
            t,=row;history.append(t);out.append(sum(t-3000<=s<=t for s in history))
        return out
    if pid==943:
        words,=args;alphabet=sorted(set(''.join(words)))
        # Enumerate all possible literal strings in increasing length; no pairwise overlap or subset DP.
        for length in range(max(map(len,words)),sum(map(len,words))+1):
            for letters in product(alphabet,repeat=length):
                s=''.join(letters)
                if all(w in s for w in words):return length
    if pid==959:
        grid,=args;n=len(grid);pixels=[[0]*(3*n) for _ in range(3*n)]
        for r,row in enumerate(grid):
            for c,ch in enumerate(row):
                if ch=='/':
                    for k in range(3):pixels[3*r+k][3*c+2-k]=1
                elif ch=='\\':
                    for k in range(3):pixels[3*r+k][3*c+k]=1
        unseen={(r,c) for r in range(3*n) for c in range(3*n) if not pixels[r][c]};regions=0
        while unseen:
            regions+=1;stack=[unseen.pop()]
            while stack:
                r,c=stack.pop()
                for p in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
                    if p in unseen:unseen.remove(p);stack.append(p)
        return regions
    raise ValueError(pid)

def compare(pid,args,result,expected):
    if pid==943:return type(result) is str and len(result)==expected and all(word in result for word in args[0])
    return type(result) is type(expected) and result==expected
