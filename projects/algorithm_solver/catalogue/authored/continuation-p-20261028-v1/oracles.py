"""Source-blind P10 independent specifications and effect witnesses.

Wire markers project real official objects; candidates never receive JSON trees.
"""
from collections import Counter
from functools import lru_cache
from itertools import product
import re

IDS=(17,37,65,87,95,99,108,114,116,117)
METHODS={17:'letterCombinations',37:'solveSudoku',65:'isNumber',87:'isScramble',95:'generateTrees',99:'recoverTree',108:'sortedArrayToBST',114:'flatten',116:'connect',117:'connect'}
KEYS={'2':'abc','3':'def','4':'ghi','5':'jkl','6':'mno','7':'pqrs','8':'tuv','9':'wxyz'}


def exact(a,b):
    if type(a) is not type(b):return False
    if type(a) is list:return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    if type(a) is dict:return set(a)==set(b) and all(exact(a[k],b[k]) for k in a)
    return a==b


def tree_nodes(marker,next_node=False):
    key='__next_node__' if next_node else '__tree_node__'
    if type(marker) is not dict or set(marker)!={key} or type(marker[key]) is not list:raise ValueError('native tree marker required')
    values=marker[key]
    if not values:return []
    if type(values[0]) is not int:raise ValueError('nonempty native tree root integer required')
    nodes=[{'value':values[0],'left':None,'right':None}];cursor=1
    for node in nodes:
        if next_node:node['next']=None
        for side in ('left','right'):
            if cursor>=len(values):continue
            value=values[cursor];cursor+=1
            if value is not None:
                if type(value) is not int:raise ValueError('strict integer node values')
                node[side]=len(nodes);nodes.append({'value':value,'left':None,'right':None})
        if len(nodes)>10000:raise ValueError('native tree representation bound')
    if cursor!=len(values):raise ValueError('unreachable tree slots')
    return nodes


def marker(nodes,root=0,next_node=False):
    key='__next_node__' if next_node else '__tree_node__'
    if not nodes or root is None:return {key:[]}
    queue=[root];values=[];seen=set()
    for node in queue:
        if node is None:values.append(None);continue
        if type(node) is not int or not 0<=node<len(nodes) or node in seen:raise ValueError('cycle or internal alias')
        seen.add(node);row=nodes[node];values.append(row['value']);queue.extend((row['left'],row['right']))
    while values and values[-1] is None:values.pop()
    return {key:values}


def traversal(nodes,order='inorder'):
    if not nodes:return []
    if order=='preorder':
        result=[];stack=[0]
        while stack:
            i=stack.pop();result.append(i)
            for side in ('right','left'):
                if nodes[i][side] is not None:stack.append(nodes[i][side])
        return result
    result=[];stack=[];i=0
    while stack or i is not None:
        while i is not None:stack.append(i);i=nodes[i]['left']
        i=stack.pop();result.append(i);i=nodes[i]['right']
    return result


def valid_number(text):
    """Literal grammar decomposition, never float parsing or candidate regex."""
    parts=re.split('[eE]',text)
    if len(parts)>2:return False
    def unsigned_sign(s):return s[1:] if s and s[0] in '+-' else s
    def digits(s):return bool(s) and all('0'<=c<='9' for c in s)
    if len(parts)==2 and not digits(unsigned_sign(parts[1])):return False
    mantissa=unsigned_sign(parts[0]);decimal=mantissa.split('.')
    if len(decimal)==1:return digits(mantissa)
    if len(decimal)!=2:return False
    a,b=decimal
    return (digits(a) and (not b or digits(b))) or (not a and digits(b))


def scrambled(a,b):
    """Bottom-up interval proof independent of delivered implementations."""
    if Counter(a)!=Counter(b):return False
    n=len(a);table={(i,j,1):a[i]==b[j] for i in range(n) for j in range(n)}
    for size in range(2,n+1):
        for i in range(n-size+1):
            for j in range(n-size+1):
                table[i,j,size]=any((table[i,j,k] and table[i+k,j+k,size-k]) or
                    (table[i,j+size-k,k] and table[i+k,j,size-k]) for k in range(1,size))
    return table[0,0,n]


@lru_cache(None)
def shapes(n):
    if not n:return (None,)
    return tuple((left,right) for size in range(n) for left in shapes(size) for right in shapes(n-1-size))


def labelled(shape,start=1):
    if shape is None:return None,start
    left,cursor=labelled(shape[0],start);value=cursor;right,cursor=labelled(shape[1],cursor+1)
    return (value,left,right),cursor


def tuple_marker(tree):
    values=[];queue=[tree] if tree is not None else []
    for node in queue:
        if node is None:values.append(None)
        else:values.append(node[0]);queue.extend((node[1],node[2]))
    while values and values[-1] is None:values.pop()
    return {'__tree_node__':values}


def sudoku_solutions(board,limit=2,node_budget=500000):
    """Exact-cover search: independently enforces four constraint families."""
    assignments={};columns={}
    for r,c,d in product(range(9),range(9),range(1,10)):
        if board[r][c]!='.' and board[r][c]!=str(d):continue
        constraints=(('cell',r,c),('row',r,d),('col',c,d),('box',3*(r//3)+c//3,d))
        assignments[r,c,d]=constraints
        for key in constraints:columns.setdefault(key,set()).add((r,c,d))
    required={('cell',r,c) for r in range(9) for c in range(9)}|{(kind,a,d) for kind in ('row','col','box') for a in range(9) for d in range(1,10)}
    result=[];visits=0
    def search(remaining,options,chosen):
        nonlocal visits
        visits+=1
        if visits>node_budget:raise ValueError('independent exact-cover budget exhausted')
        if not remaining:
            solved=[['.']*9 for _ in range(9)]
            for r,c,d in chosen:solved[r][c]=str(d)
            result.append(solved);return
        key=min(remaining,key=lambda k:len(options.get(k,())))
        for row in sorted(options.get(key,())):
            removed=set(assignments[row]);conflicts=set().union(*(options.get(k,set()) for k in removed))
            left=remaining-removed
            search(left,{k:options.get(k,set())-conflicts for k in left},chosen+[row])
            if len(result)>=limit:return
    search(required,columns,[]);return result


def validate(pid,args):
    if type(pid) is not int or pid not in IDS or type(args) is not list:raise ValueError('fixed P identity/list arguments')
    arity=2 if pid==87 else 1
    if len(args)!=arity:raise ValueError('official arity')
    a=args[0]
    if pid==17:
        if type(a) is not str or not 1<=len(a)<=4 or any(c not in KEYS for c in a):raise ValueError('official digit domain')
    elif pid==37:
        if type(a) is not list or len(a)!=9 or any(type(row) is not list or len(row)!=9 or any(type(c) is not str or len(c)!=1 or c not in '.123456789' for c in row) for row in a):raise ValueError('Sudoku character board')
        if len(sudoku_solutions(a))!=1:raise ValueError('official unique-solution domain')
    elif pid==65:
        if type(a) is not str or not 1<=len(a)<=20 or any(not('a'<=c<='z' or 'A'<=c<='Z' or '0'<=c<='9' or c in '+-.') for c in a):raise ValueError('official numeric-string domain')
    elif pid==87:
        if any(type(s) is not str or any(not 'a'<=c<='z' for c in s) for s in args) or not 1<=len(a)<=30 or len(a)!=len(args[1]):raise ValueError('official scramble domain')
    elif pid==95:
        if type(a) is not int or not 1<=a<=8:raise ValueError('official BST enumeration domain')
    elif pid==108:
        if type(a) is not list or not 1<=len(a)<=10000 or any(type(v) is not int or not -10000<=v<=10000 for v in a) or any(x>=y for x,y in zip(a,a[1:])):raise ValueError('official strictly sorted array')
    else:
        nodes=tree_nodes(a,pid in (116,117));bounds={99:(2,1000,-2**31,2**31-1),114:(0,2000,-100,100),116:(0,4095,-1000,1000),117:(0,6000,-100,100)}[pid]
        lo,hi,vlo,vhi=bounds
        if not lo<=len(nodes)<=hi or any(not vlo<=n['value']<=vhi for n in nodes):raise ValueError('official node count/value bound')
        if pid==99:
            values=[nodes[i]['value'] for i in traversal(nodes)];ordered=sorted(values);bad=[i for i,(x,y) in enumerate(zip(values,ordered)) if x!=y]
            if len(set(values))!=len(values) or len(bad)!=2 or values[bad[0]]!=ordered[bad[1]] or values[bad[1]]!=ordered[bad[0]]:raise ValueError('exactly two BST values swapped')
        if pid==116 and nodes:
            depths=[0]*len(nodes);leaves=set()
            for i,n in enumerate(nodes):
                if (n['left'] is None)!=(n['right'] is None):raise ValueError('perfect tree required')
                if n['left'] is None:leaves.add(depths[i])
                for side in ('left','right'):
                    if n[side] is not None:depths[n[side]]=depths[i]+1
            if len(leaves)!=1:raise ValueError('perfect tree leaves')


def expected(pid,args):
    validate(pid,args)
    if pid==17:return [''.join(chars) for chars in product(*(KEYS[c] for c in args[0]))]
    if pid==37:return sudoku_solutions(args[0])[0]
    if pid==65:return valid_number(args[0])
    if pid==87:return scrambled(*args)
    if pid==95:return [tuple_marker(labelled(shape)[0]) for shape in shapes(args[0])]
    if pid==108:return {'inorder':list(args[0]),'every_node_height_difference_at_most':1}
    if pid in (99,114,116,117):return effect_plan(pid,args)
    raise ValueError('unsupported P identity')


def effect_plan(pid,args):
    if pid==37:return {'board_after':sudoku_solutions(args[0])[0],'original_board_root_required':True,'original_rows_required':False,'return_void':True}
    if pid not in (99,114,116,117):raise ValueError('fixed original-node effect identity')
    nodes=tree_nodes(args[0],pid in (116,117));after=[dict(row) for row in nodes]
    if pid==99:
        values=sorted(row['value'] for row in nodes)
        for i,v in zip(traversal(nodes),values):after[i]['value']=v
    elif pid==114:
        order=traversal(nodes,'preorder')
        for position,i in enumerate(order):after[i]['left']=None;after[i]['right']=order[position+1] if position+1<len(order) else None
    else:
        levels={};depths=[0]*len(nodes)
        for i,row in enumerate(nodes):
            levels.setdefault(depths[i],[]).append(i)
            for side in ('left','right'):
                if row[side] is not None:depths[row[side]]=depths[i]+1
        for level in levels.values():
            for position,i in enumerate(level):after[i]['next']=level[position+1] if position+1<len(level) else None
    return {'before':nodes,'after':after,'argument_roots':[0 if nodes else None],'result_root':(0 if nodes else None) if pid in (116,117) else None}


def accepts_result(pid,args,result):
    """Normalized values only; native identities/classes need observer evidence."""
    if pid==17:
        return type(result) is list and all(type(s) is str for s in result) and Counter(result)==Counter(expected(pid,args))
    if pid in (65,87):return type(result) is bool and result is expected(pid,args)
    if pid in (37,99,114):return result is None
    if pid in (116,117):return exact(result,args[0])
    if pid==95:
        if type(result) is not list:return False
        try:
            forms=[tuple(tree_marker['__tree_node__']) for tree_marker in result if tree_nodes(tree_marker)]
            wanted=[tuple(t['__tree_node__']) for t in expected(pid,args)]
            return len(forms)==len(result) and Counter(forms)==Counter(wanted)
        except (TypeError,ValueError,KeyError):return False
    if pid==108:
        try:nodes=tree_nodes(result)
        except (TypeError,ValueError,KeyError):return False
        if len(nodes)!=len(args[0]) or [nodes[i]['value'] for i in traversal(nodes)]!=args[0]:return False
        heights={None:0}
        for i in reversed(range(len(nodes))):
            left,right=nodes[i]['left'],nodes[i]['right']
            if abs(heights[left]-heights[right])>1:return False
            heights[i]=1+max(heights[left],heights[right])
        return True
    return False


def check_observation(pid,args,record,language):
    """Official wrapper observation; never substitute ordinary immutable checks."""
    try:
        validate(pid,args)
        if language not in ('python','javascript') or type(record) is not dict:return False,'observation_shape'
        if 'error' in record:return False,'candidate_error'
        if type(record.get('problem_id')) is not int or record['problem_id']!=pid or record.get('method')!=METHODS[pid] or record.get('native_route')!='official-wrapper-p-v1':return False,'official_route'
        if not exact(record.get('args_before'),args):return False,'argument_before'
        result=record.get('result')
        if not accepts_result(pid,args,result):return False,'result_value'
        if pid in (37,99,114):kind='NoneType' if language=='python' else 'undefined'
        elif pid in (65,87):kind='bool' if language=='python' else 'boolean'
        elif pid in (17,95):kind='list' if language=='python' else 'object'
        elif pid==108:kind='TreeNode' if language=='python' else 'object'
        else:kind=('Node' if tree_nodes(args[0],True) else 'NoneType') if language=='python' else 'object'
        if record.get('result_type')!=kind:return False,'result_type'
        if pid==37:
            if not exact(record.get('args_after'),[expected(pid,args)]):return False,'Sudoku_board_effect'
            if not exact(record.get('board_identity'),{'argument_root_preserved':True,'before_shape':[9,9],'after_shape':[9,9]}):return False,'board_identity'
            if record.get('node_identity') is not None or record.get('node_integrity') is not None or not exact(record.get('alias_edges'),[]):return False,'unexpected_node_evidence'
            return True,None
        if record.get('board_identity') is not None:return False,'unexpected_board_evidence'
        if pid in (17,65,87):
            if not exact(record.get('args_after'),args) or not exact(record.get('alias_edges'),[]):return False,'immutable_scalar_effect'
            if record.get('node_identity') is not None or record.get('node_integrity') is not None:return False,'unexpected_node_evidence'
            return True,None
        state=record.get('node_identity')
        if type(state) is not dict or set(state)!={'before','after','argument_roots','result_root','result_roots'}:return False,'node_evidence_shape'
        after=state['after']
        if type(after) is not list:return False,'node_after_shape'
        keys={'id','value','left','right'}|({'next'} if pid in (116,117) else set())
        for i,row in enumerate(after):
            if type(row) is not dict or set(row)!=keys or type(row['id']) is not int or row['id']!=i or type(row['value']) is not int:return False,'native_node_fields'
            for side in keys-{'id','value'}:
                if row[side] is not None and (type(row[side]) is not int or not 0<=row[side]<len(after)):return False,'native_node_pointer'
        integrity={'schema':'gamma.p-official-node-integrity.v1','class_or_prototype_unchanged':True,'own_field_descriptors_unchanged':True,
                   'original_node_classes_unchanged':True,'acyclic_tree_graphs':True,'forest_cross_tree_aliases_permitted':pid==95,'checked_node_count':len(after)}
        if not exact(record.get('node_integrity'),integrity):return False,'node_physical_integrity'
        if pid in (99,114,116,117):
            plan=effect_plan(pid,args)
            wanted={**plan,'before':[{'id':i,**row} for i,row in enumerate(plan['before'])],
                    'after':[{'id':i,**row} for i,row in enumerate(plan['after'])],'result_roots':[]}
            if not exact(state,wanted):return False,'original_node_effects'
            after_args=[marker(plan['after'],0 if plan['after'] else None,pid in (116,117))]
            if not exact(record.get('args_after'),after_args):return False,'node_argument_after'
            aliases=[['result','args.0']] if pid in (116,117) and plan['after'] else []
            if not exact(record.get('alias_edges'),aliases):return False,'node_aliases'
        else:
            if not exact(record.get('args_after'),args) or not exact(record.get('alias_edges'),[]):return False,'return_tree_argument_effect'
            if not exact(state['before'],[]) or not exact(state['argument_roots'],[]):return False,'unexpected_original_nodes'
            roots=state['result_roots'] if pid==95 else [state['result_root']]
            if type(roots) is not list or (pid==95 and state['result_root'] is not None) or (pid==108 and state['result_roots']!=[]):return False,'result_roots'
            normalized=[marker(after,root) for root in roots]
            if not exact(normalized,result if pid==95 else [result]):return False,'result_physical_graph'
            used=set()
            for root in roots:
                if type(root) is not int or not 0<=root<len(after):return False,'result_root_identity'
                queue=[root];seen=set()
                for i in queue:
                    if i in seen:return False,'result_internal_alias_or_cycle'
                    seen.add(i);used.add(i)
                    for side in ('left','right'):
                        if after[i][side] is not None:queue.append(after[i][side])
            if used!=set(range(len(after))):return False,'unreachable_return_node'
        return True,None
    except (ValueError,TypeError,KeyError,IndexError,RecursionError):return False,'invalid_observation_or_domain'
