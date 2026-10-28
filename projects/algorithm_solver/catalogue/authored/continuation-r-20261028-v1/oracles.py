"""R source-blind independent class/list/profit references; no candidates."""
from copy import deepcopy

ASSIGNED_IDS=(146,147,155,156,159,160,161,163,173,188)
IDS=(146,147,155,160,173,188)
BLOCKED_IDS=(156,159,161,163)
CLASSES={146:'LRUCache',155:'MinStack',173:'BSTIterator'}
METHODS={147:'insertionSortList',160:'getIntersectionNode',188:'maxProfit'}


def exact(a,b):
    if type(a) is not type(b):return False
    if type(a) is list:return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    if type(a) is dict:return set(a)==set(b) and all(exact(a[k],b[k]) for k in a)
    return a==b


def integer(value,lo,hi):return type(value) is int and lo<=value<=hi


def list_nodes(value):
    if type(value) is not dict or set(value)!={'__list_node__'} or type(value['__list_node__']) is not list:raise ValueError('one list-node marker')
    values=value['__list_node__']
    if not 1<=len(values)<=5000 or any(not integer(v,-5000,5000) for v in values):raise ValueError('official insertion-list bounds')
    return [{'value':v,'next':i+1 if i+1<len(values) else None} for i,v in enumerate(values)]


def shared_graph(value):
    if type(value) is not dict or set(value)!={'__list_graph__'}:raise ValueError('shared physical list graph marker')
    graph=value['__list_graph__']
    if type(graph) is not dict or set(graph)!={'nodes','argument_roots'}:raise ValueError('exact shared list graph')
    nodes=graph['nodes'];roots=graph['argument_roots']
    if type(nodes) is not list or not 1<=len(nodes)<=60000 or type(roots) is not list or len(roots)!=2 or any(not integer(r,0,len(nodes)-1) for r in roots):raise ValueError('two nonempty physical list roots')
    for row in nodes:
        if type(row) is not dict or set(row)!={'value','next'} or not integer(row['value'],1,100000) or row['next'] is not None and not integer(row['next'],0,len(nodes)-1):raise ValueError('shared ListNode fields')
    paths=[];all_seen=set()
    for root in roots:
        path=[];seen=set();i=root
        while i is not None:
            if i in seen:raise ValueError('cyclic list outside official domain')
            seen.add(i);all_seen.add(i);path.append(i);i=nodes[i]['next']
            if len(path)>30000:raise ValueError('official list length bound')
        paths.append(path)
    if all_seen!=set(range(len(nodes))):raise ValueError('unreachable list wire nodes')
    return nodes,roots,paths


def tree_nodes(value):
    if type(value) is not dict or set(value)!={'__tree_node__'} or type(value['__tree_node__']) is not list:raise ValueError('iterator constructor tree marker')
    values=value['__tree_node__']
    if not values or not integer(values[0],0,1000000):raise ValueError('nonempty iterator BST')
    nodes=[{'value':values[0],'left':None,'right':None}];cursor=1
    for node in nodes:
        for side in ('left','right'):
            if cursor>=len(values):continue
            v=values[cursor];cursor+=1
            if v is not None:
                if not integer(v,0,1000000):raise ValueError('iterator node value')
                node[side]=len(nodes);nodes.append({'value':v,'left':None,'right':None})
        if len(nodes)>100000:raise ValueError('iterator node count bound')
    if cursor!=len(values):raise ValueError('unreachable iterator tree tokens')
    ordered=inorder(nodes)
    if any(x>=y for x,y in zip(ordered,ordered[1:])):raise ValueError('strict BST input')
    return nodes


def inorder(nodes):
    values=[];stack=[];i=0 if nodes else None
    while stack or i is not None:
        while i is not None:stack.append(i);i=nodes[i]['left']
        i=stack.pop();values.append(nodes[i]['value']);i=nodes[i]['right']
    return values


def class_trace(pid,args):
    if type(args) is not list or len(args)!=2:raise ValueError('operations and constructor/method arguments')
    operations,rows=args
    if type(operations) is not list or type(rows) is not list or len(operations)!=len(rows) or not operations or operations[0]!=CLASSES[pid] or any(type(row) is not list for row in rows):raise ValueError('one original class constructor')
    bound={146:200000,155:30000,173:100000}[pid]
    if len(operations)-1>bound:raise ValueError('official method-call bound')
    if pid==146:
        if len(rows[0])!=1 or not integer(rows[0][0],1,3000):raise ValueError('positive LRU capacity')
        capacity=rows[0][0];entries=[];outputs=[None]
        for name,row in zip(operations[1:],rows[1:]):
            if name=='get' and len(row)==1 and integer(row[0],0,10000):
                index=next((i for i,pair in enumerate(entries) if pair[0]==row[0]),None)
                if index is None:outputs.append(-1)
                else:pair=entries.pop(index);entries.append(pair);outputs.append(pair[1])
            elif name=='put' and len(row)==2 and integer(row[0],0,10000) and integer(row[1],0,100000):
                entries=[pair for pair in entries if pair[0]!=row[0]];entries.append(tuple(row));entries=entries[-capacity:];outputs.append(None)
            else:raise ValueError('exact LRU method domain')
        return outputs
    if pid==155:
        if rows[0]!=[]:raise ValueError('zero-argument MinStack constructor')
        stack=[];outputs=[None]
        for name,row in zip(operations[1:],rows[1:]):
            if name=='push' and len(row)==1 and integer(row[0],-2**31,2**31-1):stack.append(row[0]);outputs.append(None)
            elif name in ('pop','top','getMin') and not row and stack:
                if name=='pop':stack.pop();outputs.append(None)
                else:outputs.append(stack[-1] if name=='top' else min(stack))
            else:raise ValueError('valid nonempty stack methods only')
        return outputs
    if len(rows[0])!=1:raise ValueError('BSTIterator(root) constructor')
    values=inorder(tree_nodes(rows[0][0]));position=0;outputs=[None]
    for name,row in zip(operations[1:],rows[1:]):
        if row:raise ValueError('iterator zero-arity methods')
        if name=='hasNext':outputs.append(position<len(values))
        elif name=='next' and position<len(values):outputs.append(values[position]);position+=1
        else:raise ValueError('valid iterator methods only')
    return outputs


def validate(pid,args):
    if type(pid) is not int or pid not in IDS or type(args) is not list:raise ValueError('available fixed R identities only')
    if pid in CLASSES:class_trace(pid,args);return
    if pid==147:
        if len(args)!=1:raise ValueError('official list method arity')
        list_nodes(args[0]);return
    if pid==160:
        if len(args)!=1:raise ValueError('one shared graph projects two real head arguments')
        shared_graph(args[0]);return
    if len(args)!=2 or not integer(args[0],1,100) or type(args[1]) is not list or not 1<=len(args[1])<=1000 or any(not integer(v,0,1000) for v in args[1]):raise ValueError('official k/prices bounds')


def profit(k,prices):
    """Backward day/action induction, never language agreement or candidate calls."""
    free=[0]*(k+1);holding=[-10**9]*(k+1)
    for price in reversed(prices):
        free,holding=([max(free[t],-price+holding[t]) for t in range(k+1)],
                      [max(holding[t],price+free[t-1]) if t else -10**9 for t in range(k+1)])
    return free[k]


def expected(pid,args):
    validate(pid,args)
    if pid in CLASSES:return class_trace(pid,args)
    if pid==147:return {'__list_node__':sorted(args[0]['__list_node__'])}
    if pid==160:
        nodes,roots,paths=shared_graph(args[0]);other=set(paths[1]);return next((i for i in paths[0] if i in other),None)
    return profit(*args)


def effect_contract(pid,args):
    validate(pid,args)
    if pid==147:
        nodes=list_nodes(args[0])
        return {'before':nodes,'argument_roots':[0],'same_physical_nodes_required':True,'values_preserved_per_id':True,'result':'acyclic permutation of every original node, nondecreasing values','tie_order':'not constrained; stability not required by available definition','algorithmic_gate':'insertion sort required by body, independently reviewed, not inferred from sorted output'}
    if pid==160:
        nodes,roots,_=shared_graph(args[0]);return {'before':nodes,'after':deepcopy(nodes),'argument_roots':roots,'result_root':expected(pid,args),'new_nodes_allowed':False}
    if pid==173:return {'constructor_tree_before':tree_nodes(args[1][0][0]),'constructor_tree_after':'unchanged under explicit local prospective nonmutating variant contract; not asserted as an official universal requirement','class_state_mutation':'permitted; persistent original receiver per trace'}
    if pid in (146,155):return {'trace_arguments':'unchanged','class_state_mutation':'permitted; persistent original receiver per trace'}
    return {'arguments':'unchanged','result_type':'strict integer','mutable_return_aliases':False}


def accepts_result(pid,args,value):
    return exact(value,expected(pid,args))


def accepts_list_identity(args,state):
    """147 identity check deliberately permits either equal-value tie order."""
    try:
        before=list_nodes(args[0]);after=state['after'];root=state['result_root'];n=len(before)
        if not exact(state['before'],[{'id':i,**row} for i,row in enumerate(before)]) or not exact(state['argument_roots'],[0]) or type(after) is not list or len(after)!=n:return False
        for i,row in enumerate(after):
            if type(row) is not dict or set(row)!={'id','value','next'} or type(row['id']) is not int or row['id']!=i or not exact(row['value'],before[i]['value']) or row['next'] is not None and not integer(row['next'],0,n-1):return False
        seen=set();values=[];i=root
        while i is not None:
            if not integer(i,0,n-1) or i in seen:return False
            seen.add(i);values.append(after[i]['value']);i=after[i]['next']
        return seen==set(range(n)) and values==sorted(values)
    except (ValueError,TypeError,KeyError,IndexError):return False


def accepts_intersection_identity(args,state):
    try:
        nodes,roots,_=shared_graph(args[0]);wanted=[{'id':i,**row} for i,row in enumerate(nodes)]
        return (type(state) is dict and exact(state.get('before'),wanted) and exact(state.get('after'),wanted) and exact(state.get('argument_roots'),roots) and exact(state.get('result_root'),expected(160,args)))
    except (ValueError,TypeError,KeyError,IndexError):return False


def class_return_types(pid,args,language):
    validate(pid,args)
    if pid not in CLASSES or language not in ('python','javascript'):raise ValueError('class/language contract')
    result=['constructed']
    for method in args[0][1:]:
        if pid==146 and method=='put' or pid==155 and method in ('push','pop'):result.append('NoneType' if language=='python' else 'undefined')
        elif pid==173 and method=='hasNext':result.append('bool' if language=='python' else 'boolean')
        else:result.append('int' if language=='python' else 'number')
    return result
