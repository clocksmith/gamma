"""Local development transports and result predicates; not a qualification judge."""
from collections import Counter,deque
from types import SimpleNamespace
import copy,json,math
TREE_IDS={968,979,987,993,1022,1038,1110}
class Mountain:
    def __init__(self,values):self.values=tuple(values);self.calls=0
    def get(self,index):
        if not 0<=index<len(self.values):raise AssertionError('invalid MountainArray index')
        self.calls+=1
        if self.calls>100:raise AssertionError('MountainArray exceeded100 get calls')
        return self.values[index]
    def length(self):return len(self.values)

def binary(values):
    if not values:return None
    root=SimpleNamespace(val=values[0],left=None,right=None);q=deque([root]);i=1
    while q and i<len(values):
        n=q.popleft()
        for side in ('left','right'):
            if i==len(values):break
            v=values[i];i+=1
            if v is not None:c=SimpleNamespace(val=v,left=None,right=None);setattr(n,side,c);q.append(c)
    return root

def linked(values):
    node=None
    for v in reversed(values):node=SimpleNamespace(val=v,next=node)
    return node

def native(pid,args):
    values=copy.deepcopy(args)
    if pid in TREE_IDS:values[0]=binary(values[0])
    elif pid==1019:values[0]=linked(values[0])
    elif pid==1669:values[0]=linked(values[0]);values[3]=linked(values[3])
    elif pid==1095:values[1]=Mountain(values[1])
    return values

def nodes(root,kind='tree'):
    stack=[] if root is None else [root];out=[];seen=set()
    while stack:
        n=stack.pop()
        if id(n) in seen:raise AssertionError('cycle/shared output node')
        seen.add(id(n));out.append(n);stack.extend(c for c in ([n.next] if kind=='list' else [n.left,n.right]) if c is not None)
    return out

def effects(pid,args):
    roots=[args[0]] if pid in TREE_IDS or pid==1019 else [args[0],args[3]] if pid==1669 else [];kind='list' if pid in (1019,1669) else 'tree';out=[];ids=set()
    for root in roots:
        for n in nodes(root,kind):ids.add(id(n));out.append((id(n),n.val,tuple(id(c) if c is not None else None for c in ([n.next] if kind=='list' else [n.left,n.right]))))
    if roots:return out,ids
    if pid==1095:return (args[0],args[1].values),set()
    return copy.deepcopy(args),set()

def serial(root):
    if root is None:return []
    nodes(root);out=[];q=deque([root])
    while q:
        n=q.popleft()
        if n is None:out.append(None)
        else:out.append(n.val);q.extend([n.left,n.right])
    while out and out[-1] is None:out.pop()
    return out

def normalize(pid,result,input_ids):
    if pid in (1028,1038,1110,1669):
        roots=result if pid==1110 else [result];seen=set()
        for root in roots:
            for n in nodes(root,'list' if pid==1669 else 'tree'):
                if id(n) in input_ids or id(n) in seen:raise AssertionError('fresh output aliases input/another component')
                seen.add(id(n))
    if pid in (1028,1038):return serial(result)
    if pid==1110:return sorted([serial(n) for n in result],key=repr)
    if pid==1669:return [n.val for n in nodes(result,'list')]
    return result

def matches(pid,actual,expected,args):
    if pid==963:return isinstance(actual,(float,int)) and abs(actual-expected)<=1e-5
    if pid==969:
        a=args[0].copy()
        if not isinstance(actual,list) or len(actual)>10*len(a):return False
        for k in actual:
            if type(k)is not int or not 1<=k<=len(a):return False
            a[:k]=reversed(a[:k])
        return a==sorted(args[0])
    if pid==984:return isinstance(actual,str) and len(actual)==sum(args) and Counter(actual)==Counter({'a':args[0],'b':args[1]}) and 'aaa' not in actual and 'bbb' not in actual
    if pid==1054:return isinstance(actual,list) and Counter(actual)==Counter(args[0]) and all(a!=b for a,b in zip(actual,actual[1:]))
    if pid==1138:
        if not isinstance(actual,str):return False
        r=c=0;word=[]
        for token in actual:
            if token=='!':word.append(chr(97+r*5+c));continue
            if token not in 'UDLR':return False
            dr,dc={'U':(-1,0),'D':(1,0),'L':(0,-1),'R':(0,1)}[token];r+=dr;c+=dc
            if not(0<=r<=5 and 0<=c<5 and (r<5 or c==0)):return False
        need=0;last=(0,0)
        for ch in args[0]:p=divmod(ord(ch)-97,5);need+=abs(p[0]-last[0])+abs(p[1]-last[1])+1;last=p
        return ''.join(word)==args[0] and len(actual)==need
    if pid==1718 and isinstance(expected,dict):
        n=args[0]
        if len(actual)!=2*n-1 or Counter(actual)!=Counter([1]+[v for v in range(2,n+1) for _ in range(2)]):return False
        return all(actual.index(v)+v<len(actual) and actual[actual.index(v)+v]==v for v in range(2,n+1))
    return json.dumps(actual,sort_keys=True)==json.dumps(expected,sort_keys=True)
