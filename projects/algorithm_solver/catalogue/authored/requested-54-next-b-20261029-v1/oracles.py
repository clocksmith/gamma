"""Small independent references; never called on maximum-boundary cases."""
from functools import lru_cache

class TreeNode:
    def __init__(self,val=0,left=None,right=None):
        self.val,self.left,self.right=val,left,right

def decode_tree(values):
    root=TreeNode(values[0]);queue=[root];index=1
    for node in queue:
        for side in ['left','right']:
            if index>=len(values):break
            value=values[index];index+=1
            if value is not None:
                child=TreeNode(value);setattr(node,side,child);queue.append(child)
    assert index==len(values)
    return root

def encode_tree(root):
    queue=[root];values=[]
    for node in queue:
        if node is None:values.append(None)
        else:values.append(node.val);queue.extend([node.left,node.right])
    while values and values[-1] is None:values.pop()
    return values

def best_free(n,occupied):
    return max((seat for seat in range(n) if seat not in occupied),key=lambda x:(min((abs(x-y) for y in occupied),default=n),-x))

def validate_domain(pid,args):
    def integer(x,lo,hi):assert type(x) is int and lo<=x<=hi
    if pid==855:
        ops,rows=args;assert ops[0]=='ExamRoom' and len(rows[0])==1;integer(rows[0][0],1,10**9);assert len(ops)==len(rows) and len(ops)-1<=10000
        count=0
        for op,row in zip(ops[1:],rows[1:]):
            if op=='seat':assert row==[] and count<rows[0][0];count+=1
            else:assert op=='leave' and len(row)==1;integer(row[0],0,rows[0][0]-1);assert count>0;count-=1
        # Actual legal leave identities are independently replayed for all small cases.
    elif pid==863:
        values,target,k=args;assert 1<=sum(x is not None for x in values)<=500;actual=[x for x in values if x is not None];assert len(actual)==len(set(actual)) and target in actual
        for x in actual:integer(x,0,500)
        integer(k,0,1000);decode_tree(values)
    elif pid==887:
        k,n=args;integer(k,1,100);integer(n,1,10000)
    elif pid==900:
        ops,rows=args;assert ops[0]=='RLEIterator' and len(rows[0])==1;encoding=rows[0][0];assert len(encoding)%2==0 and 2<=len(encoding)<=1000
        for x in encoding:integer(x,0,10**9)
        assert len(ops)==len(rows) and len(ops)-1<=1000
        for op,row in zip(ops[1:],rows[1:]):assert op=='next' and len(row)==1;integer(row[0],1,10**9)
    elif pid==901:
        ops,rows=args;assert ops[0]=='StockSpanner' and rows[0]==[] and len(ops)==len(rows) and len(ops)-1<=10000
        for op,row in zip(ops[1:],rows[1:]):assert op=='next' and len(row)==1;integer(row[0],1,100000)
    else:raise ValueError(pid)

def reference(pid,args):
    validate_domain(pid,args)
    if pid==855:
        ops,rows=args;n=rows[0][0];occupied=set();out=[None]
        for op,row in zip(ops[1:],rows[1:]):
            if op=='seat':value=best_free(n,occupied);occupied.add(value);out.append(value)
            else:assert row[0] in occupied;occupied.remove(row[0]);out.append(None)
        return out
    if pid==863:
        values,target,k=args;root=decode_tree(values);paths={};stack=[(root,())]
        while stack:
            node,path=stack.pop();path=path+(node.val,);paths[node.val]=path
            for child in [node.left,node.right]:
                if child is not None:stack.append((child,path))
        wanted=paths[target];result=[]
        for value,path in paths.items():
            common=0
            for a,b in zip(path,wanted):
                if a!=b:break
                common+=1
            if len(path)+len(wanted)-2*common==k:result.append(value)
        return result
    if pid==887:
        eggs,floors=args
        @lru_cache(None)
        def minimax(e,n):
            if n<=1 or e==1:return n
            return 1+min(max(minimax(e-1,x-1),minimax(e,n-x)) for x in range(1,n+1))
        return minimax(eggs,floors)
    if pid==900:
        ops,rows=args;encoding=rows[0][0];literal=[v for count,v in zip(encoding[::2],encoding[1::2]) for _ in range(count)];position=0;out=[None]
        for row in rows[1:]:position+=row[0];out.append(literal[position-1] if position<=len(literal) else -1)
        return out
    if pid==901:
        ops,rows=args;prices=[];out=[None]
        for row in rows[1:]:
            price=row[0];prices.append(price);span=0
            for value in reversed(prices):
                if value>price:break
                span+=1
            out.append(span)
        return out

def compare(pid,result,expected):
    if pid==863:return type(result) is list and len(result)==len(set(result)) and sorted(result)==sorted(expected)
    return type(result) is type(expected) and result==expected
