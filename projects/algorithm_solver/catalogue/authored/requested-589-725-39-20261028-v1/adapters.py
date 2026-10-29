"""Development-only official object adapters and output/effect observers."""
from collections import deque
from types import SimpleNamespace
import copy
import json

TREE_IDS={606,617,623,637,652,653,655,662,671,687,700,701}
FRESH_IDS={617,623,701,725}


def binary(values):
    if not values:return None
    root=SimpleNamespace(val=values[0],left=None,right=None);queue=deque([root]);at=1
    while queue and at<len(values):
        node=queue.popleft()
        for side in ('left','right'):
            if at>=len(values):break
            value=values[at];at+=1
            if value is not None:
                child=SimpleNamespace(val=value,left=None,right=None);setattr(node,side,child);queue.append(child)
    return root


def native(pid,args):
    args=copy.deepcopy(args)
    if pid in TREE_IDS:
        args[0]=binary(args[0])
        if pid==617:args[1]=binary(args[1])
    elif pid in (589,590):
        r=args[0];nodes=[SimpleNamespace(val=v,children=[]) for v in r['values']]
        for i,children in enumerate(r['children']):nodes[i].children=[nodes[j] for j in children]
        args=[nodes[0] if nodes else None]
    elif pid==690:args[0]=[SimpleNamespace(id=i,importance=v,subordinates=s) for i,v,s in args[0]]
    elif pid==725:
        head=None
        for value in reversed(args[0]):head=SimpleNamespace(val=value,next=head)
        args[0]=head
    return args


def graph_nodes(root,kind='tree'):
    stack=[root] if root is not None else [];out=[];seen=set()
    while stack:
        node=stack.pop()
        if id(node) in seen:raise AssertionError('cycle or shared node in tree/list output')
        seen.add(id(node));out.append(node)
        children=node.children if kind=='nary' else [node.next] if kind=='list' else [node.left,node.right]
        stack.extend(c for c in children if c is not None)
    return out


def effects(pid,args):
    roots=[args[0]]+([args[1]] if pid==617 else []) if pid in TREE_IDS else [args[0]] if pid in (589,590,725) else []
    kind='nary' if pid in (589,590) else 'list' if pid==725 else 'tree'
    records=[];identities=set()
    for root in roots:
        for node in graph_nodes(root,kind):
            identities.add(id(node));edges=node.children if kind=='nary' else [node.next] if kind=='list' else [node.left,node.right]
            records.append((id(node),node.val,tuple(id(c) if c is not None else None for c in edges)))
    if roots:return (records,identities)
    if pid==690:return ([(e.id,e.importance,tuple(e.subordinates)) for e in args[0]],set())
    return (copy.deepcopy(args),set())


def serial(root):
    if root is None:return []
    graph_nodes(root);queue=deque([root]);out=[]
    while queue:
        n=queue.popleft()
        if n is None:out.append(None)
        else:out.append(n.val);queue.extend([n.left,n.right])
    while out and out[-1] is None:out.pop()
    return out


def normalize(pid,result,input_ids):
    if pid in FRESH_IDS:
        roots=result if pid==725 else [result]
        output_ids=[]
        for root in roots:output_ids.extend(id(n) for n in graph_nodes(root,'list' if pid==725 else 'tree'))
        assert not input_ids.intersection(output_ids),'output aliases read-only input where fresh output is promised'
        assert len(output_ids)==len(set(output_ids)),'fresh output parts share nodes'
    if pid in (617,623,654,700):return serial(result)
    if pid==652:
        shapes=[serial(root) for root in result]
        assert len({json.dumps(s) for s in shapes})==len(shapes),'duplicate output representatives'
        return sorted(shapes,key=repr)
    if pid==701:
        graph_nodes(result);out=[];stack=[];node=result
        while node is not None or stack:
            while node is not None:stack.append(node);node=node.left
            node=stack.pop();out.append(node.val);node=node.right
        assert all(out[i]<out[i+1] for i in range(len(out)-1)),'result is not a strict BST'
        return out
    if pid==725:return [[node.val for node in graph_nodes(head,'list')] for head in result]
    if pid==721:return sorted(result)
    return result


def matches(pid,actual,expected,args):
    if pid==637:return len(actual)==len(expected) and all(abs(a-b)<=1e-5 for a,b in zip(actual,expected))
    if pid==710:
        n,black=args[1][0];blocked=set(black);draws=actual[1:]
        if len(actual)!=len(args[0]) or actual[0] is not None or any(type(v) is not int or not 0<=v<n or v in blocked for v in draws):return False
        if n<=100 and len(draws)==n-len(black):return sorted(draws)==[v for v in range(n) if v not in blocked]
        return True
    return actual==expected
