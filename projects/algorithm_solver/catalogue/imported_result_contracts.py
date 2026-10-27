"""Statement-specific result checks for nonunique answers and node transports.

These host-side checks never enter the candidate sandbox. They do not decide
which inputs are admissible; that independent decision precedes execution.
"""
from collections import Counter, deque
import math

STRING_SETS = {282,472,784,884,2933}
INTEGER_SETS = {1606,2951}
FLOAT_TOLERANCES = {813:1e-6,1377:1e-5,1701:1e-5,3194:0.0}
NODE_RETURNS = {814:'TreeNode',876:'ListNode',998:'TreeNode',1008:'TreeNode',
                1382:'TreeNode',2074:'ListNode',2196:'TreeNode',2415:'TreeNode',2807:'ListNode',2816:'ListNode'}


def canonical(value):
    """Encode lossless integers and normalize only redundant null tree padding."""
    if type(value)is int and abs(value)>2**53-1:
        return {'__gamma_bigint_v1__':str(value)}
    if type(value)is list:
        return [canonical(v)for v in value]
    if type(value)is dict:
        if set(value)=={'__tree_node__'}:
            values=list(value['__tree_node__'])
            while values and values[-1]is None:values.pop()
            return {'__tree_node__':canonical(values)} if values else None
        if set(value)=={'__list_node__'} and value['__list_node__']==[]:
            return None
        return {k:canonical(v)for k,v in value.items()}
    return value


def exact(left,right):
    if type(left)is not type(right):return False
    if type(left)is list:return len(left)==len(right) and all(exact(x,y)for x,y in zip(left,right))
    if type(left)is dict:return left.keys()==right.keys() and all(exact(left[k],right[k])for k in left)
    return left==right


def tree(encoded):
    """Return values/children, rejecting unreachable or malformed serialization."""
    if type(encoded)is not dict or set(encoded)!={'__tree_node__'}:raise ValueError('tree marker required')
    data=encoded['__tree_node__']
    if type(data)is not list or not data or type(data[0])is not int:raise ValueError('nonempty integer tree required')
    values=[data[0]];children=[];cursor=1;index=0
    while index<len(values):
        pair=[]
        for _ in range(2):
            item=data[cursor] if cursor<len(data) else None;cursor+=1
            if item is None:pair.append(None)
            elif type(item)is int:pair.append(len(values));values.append(item)
            else:raise ValueError('integer tree values required')
        children.append(pair);index+=1
    if any(v is not None for v in data[cursor:]):raise ValueError('unreachable tree nodes')
    return values,children


def balanced_same_bst(got,original):
    try:
        values,children=tree(got);old,_=tree(original)
    except ValueError:return False
    if sorted(values)!=sorted(old):return False
    stack=[(0,None,None)];heights=[0]*len(values)
    while stack:
        i,low,high=stack.pop();v=values[i]
        if (low is not None and v<=low)or(high is not None and v>=high):return False
        left,right=children[i]
        if left is not None:stack.append((left,low,v))
        if right is not None:stack.append((right,v,high))
    for i in range(len(values)-1,-1,-1):
        left,right=children[i];lh=0 if left is None else heights[left];rh=0 if right is None else heights[right]
        if abs(lh-rh)>1:return False
        heights[i]=max(lh,rh)+1
    return True


def cyclic(n, edges):
    successors=[set() for _ in range(n)]; degree=[0]*n
    for u,v in edges:
        if v not in successors[u]:successors[u].add(v);degree[v]+=1
    queue=deque(i for i,d in enumerate(degree)if d==0);seen=0
    while queue:
        u=queue.popleft();seen+=1
        for v in successors[u]:
            degree[v]-=1
            if degree[v]==0:queue.append(v)
    return seen!=n


def stamp_possible(stamp,target):
    dependencies=[];waiting=[[]for _ in target];queue=deque()
    for i in range(len(target)-len(stamp)+1):
        mismatch={i+j for j,c in enumerate(stamp)if target[i+j]!=c}
        dependencies.append(mismatch)
        for j in mismatch:waiting[j].append(i)
        if not mismatch:queue.append(i)
    erased=set()
    while queue:
        i=queue.popleft()
        for j in range(i,i+len(stamp)):
            if j in erased:continue
            erased.add(j)
            for window in waiting[j]:
                dependencies[window].discard(j)
                if not dependencies[window]:queue.append(window)
    return len(erased)==len(target)


def grouping_impossible(n,m,groups,before):
    own=list(groups)
    for i,g in enumerate(own):
        if g==-1:own[i]=m;m+=1
    item_edges=[(u,v)for v,edges in enumerate(before)for u in edges]
    group_edges=[(own[u],own[v])for u,v in item_edges if own[u]!=own[v]]
    return cyclic(n,item_edges) or cyclic(m,group_edges)


def semantic_value(pid,args,got,wanted):
    if pid in STRING_SETS:
        return type(got)is list and all(type(v)is str for v in got) and len(got)==len(set(got)) and set(got)==set(wanted)
    if pid in INTEGER_SETS:
        return type(got)is list and all(type(v)is int for v in got) and len(got)==len(set(got)) and set(got)==set(wanted)
    if pid in FLOAT_TOLERANCES and FLOAT_TOLERANCES[pid] is not None:
        return type(got)in(int,float) and math.isfinite(got) and abs(got-wanted)<=FLOAT_TOLERANCES[pid]
    if pid==767:
        s=args[0]
        return type(got)is str and ((got=='' and max(Counter(s).values())>(len(s)+1)//2)or(Counter(got)==Counter(s) and all(x!=y for x,y in zip(got,got[1:]))))
    if pid==936:
        stamp,target=args
        if type(got)is not list or any(type(v)is not int for v in got)or len(got)>10*len(target):return False
        if not got:return not stamp_possible(stamp,target)
        canvas=['?']*len(target)
        for pos in got:
            if not 0<=pos<=len(target)-len(stamp):return False
            canvas[pos:pos+len(stamp)]=stamp
        return ''.join(canvas)==target
    if pid==1203:
        n,m,groups,before=args
        if type(got)is not list or any(type(v)is not int for v in got):return False
        if not got:return grouping_impossible(n,m,groups,before)
        if sorted(got)!=list(range(n)):return False
        position={v:i for i,v in enumerate(got)}
        if any(position[u]>=position[v]for v,edges in enumerate(before)for u in edges):return False
        spans={}
        for i,v in enumerate(got):
            if groups[v]!=-1:spans.setdefault(groups[v],[]).append(i)
        return all(xs[-1]-xs[0]+1==len(xs)for xs in spans.values())
    if pid==1382:return balanced_same_bst(got,args[0])
    if pid==1489:
        return type(got)is list and len(got)==2 and all(type(xs)is list and all(type(v)is int for v in xs) and len(xs)==len(set(xs)) and set(xs)==set(ys)for xs,ys in zip(got,wanted))
    if pid==1548:
        n,roads,names,target=args
        if type(got)is not list or len(got)!=len(target) or any(type(v)is not int or not 0<=v<n for v in got):return False
        edges={tuple(sorted(e))for e in roads}
        if any(tuple(sorted(e))not in edges for e in zip(got,got[1:])):return False
        # Independently derive the optimum from the statement's path objective.
        costs=[int(name!=target[0])for name in names]
        for letter in target[1:]:
            nxt=[len(target)+1]*n
            for u,v in roads:
                nxt[v]=min(nxt[v],costs[u]+(names[v]!=letter));nxt[u]=min(nxt[u],costs[v]+(names[u]!=letter))
            costs=nxt
        return sum(names[v]!=letter for v,letter in zip(got,target))==min(costs)
    if pid==1901:
        grid=args[0]
        if type(got)is not list or len(got)!=2 or any(type(v)is not int for v in got):return False
        r,c=got;m,n=len(grid),len(grid[0])
        return 0<=r<m and 0<=c<n and all(grid[r][c]>grid[i][j]for i,j in((r-1,c),(r+1,c),(r,c-1),(r,c+1))if 0<=i<m and 0<=j<n)
    if pid==1948:
        if type(got)is not list or any(type(row)is not list or any(type(v)is not str for v in row)for row in got):return False
        result=[tuple(r)for r in got]
        return len(result)==len(set(result)) and set(result)=={tuple(r)for r in wanted}
    if pid==1982:
        n,sums=args
        if type(got)is not list or len(got)!=n or any(type(v)is not int or not -10000<=v<=10000 for v in got):return False
        values=[0]
        for x in got:values += [v+x for v in values]
        return Counter(values)==Counter(sums)
    if pid==2007:
        changed=args[0]
        if type(got)is not list or any(type(x)is not int or x<0 for x in got):return False
        if got:return Counter(got+[2*x for x in got])==Counter(changed)
        if len(changed)%2:return True
        counts=Counter(changed)
        for x in sorted(counts):
            if counts[x]==0:continue
            if x==0:
                if counts[x]%2:return True
                counts[x]=0
            else:
                count=counts[x]
                if counts[2*x]<count:return True
                counts[2*x]-=count;counts[x]=0
        return False
    if pid==2392:
        k,above,left=args
        if type(got)is not list:return False
        if not got:return cyclic(k,[(u-1,v-1)for u,v in above]) or cyclic(k,[(u-1,v-1)for u,v in left])
        if len(got)!=k or any(type(row)is not list or len(row)!=k or any(type(v)is not int or not 0<=v<=k for v in row)for row in got):return False
        places={};count=0
        for r,row in enumerate(got):
            for c,v in enumerate(row):
                if v:places[v]=(r,c);count+=1
        return count==k and set(places)==set(range(1,k+1)) and all(places[u][0]<places[v][0]for u,v in above) and all(places[u][1]<places[v][1]for u,v in left)
    if pid==2733:
        xs=args[0]
        return type(got)is int and ((got==-1 and len(xs)<3)or(got in xs and min(xs)<got<max(xs)))
    return exact(canonical(got),canonical(wanted))


def compare(pid,case,record,language):
    if 'error'in record:return 'candidate_error'
    wanted=case['expected'];got=record.get('result');kind=record.get('result_type')
    if pid in FLOAT_TOLERANCES and FLOAT_TOLERANCES[pid]is not None:
        correct_kind=kind in(('int','float')if language=='python'else('number',))
    elif pid in NODE_RETURNS and canonical(wanted)is not None:
        correct_kind=kind==(NODE_RETURNS[pid]if language=='python'else'object')
    else:
        expected=canonical(wanted)
        if type(expected)is dict and set(expected)=={'__gamma_bigint_v1__'}:
            correct_kind=kind==('int'if language=='python'else'bigint')
        else:
            types={type(None):('NoneType','object'),bool:('bool','boolean'),int:('int','number'),float:('float','number'),str:('str','string'),list:('list','object'),dict:('dict','object')}
            correct_kind=kind==types[type(expected)][language=='javascript']
    if not correct_kind:return 'result_type'
    try:same=semantic_value(pid,case['args'],got,wanted)
    except (TypeError,ValueError,IndexError,KeyError,OverflowError):same=False
    if not same:return 'result_value'
    if pid in (814,2074,2415,2807):
        from .node_identity_contracts import check
        return check(pid,case['args'],record,exact,canonical)
    before=canonical(case['args'])
    if not exact(record.get('args_before'),before)or not exact(record.get('args_after'),before):return 'input_effects'
    aliases=[]
    if pid==876:
        length=len(case['args'][0]['__list_node__'])
        aliases=[['result','args.0'+'.next'*(length//2)]]
    if not exact(record.get('alias_edges'),aliases):return 'return_aliases'
    return None
