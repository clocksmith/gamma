"""T source-blind independent references; premium243/245 excluded, never replaced."""
from collections import deque
REQUESTED_IDS=(226,230,232,233,234,235,236,237,243,245)
IDS=(226,230,232,233,234,235,236,237)
BLOCKED_IDS={243:'Officialpremiumdefinition',245:'Officialpremiumdefinition'}

def integer(x,lo,hi):return type(x) is int and lo<=x<=hi

def exact(a,b):
    if type(a) is not type(b):return False
    if type(a) is list:return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    if type(a) is dict:return a.keys()==b.keys() and all(exact(a[k],b[k]) for k in a)
    return a==b

def tree_order(p):
    n=len(p['values']);todo=[] if p['root'] is None else[p['root']];seen=set()
    for i in todo:
        if not integer(i,0,n-1) or i in seen:raise ValueError('treeindex/alias/cycle')
        seen.add(i);todo.extend(j for j in (p['left'][i],p['right'][i]) if j is not None)
    if len(seen)!=n:raise ValueError('unreachablepool')
    return todo

def list_order(p):
    order=[];seen=set();i=p['head'];n=len(p['values'])
    while i is not None:
        if not integer(i,0,n-1) or i in seen:raise ValueError('listcycle/index')
        order.append(i);seen.add(i);i=p['next'][i]
    if len(order)!=n:raise ValueError('unreachablelistpool')
    return order

def validate(pid,args):
    if type(pid) is not int or pid not in IDS or type(args) is not list:raise ValueError('fixedactiveidentity;premium243/245excluded')
    arity=3 if pid in (235,236) else 2 if pid in (230,232,237) else 1
    if len(args)!=arity:raise ValueError('arity')
    p=args[0]
    if pid in (226,230,235,236):
        cap=100 if pid==226 else 10000 if pid==230 else 100000;lo=-100 if pid==226 else 0 if pid==230 else -10**9;hi=100 if pid==226 else 10000 if pid==230 else 10**9
        if type(p) is not dict or set(p)!={'values','left','right','root'} or type(p['values']) is not list or not(0 if pid==226 else 1 if pid==230 else 2)<=len(p['values'])<=cap or not all(integer(v,lo,hi) for v in p['values']):raise ValueError('treevalues')
        n=len(p['values'])
        if any(type(p[k]) is not list or len(p[k])!=n or any(x is not None and not integer(x,0,n-1) for x in p[k]) for k in ('left','right')) or(p['root'] is not None and not integer(p['root'],0,n-1)):raise ValueError('treeedges')
        tree_order(p)
        if pid in (230,235):
            stack=[];node=p['root'];previous=None
            while stack or node is not None:
                while node is not None:stack.append(node);node=p['left'][node]
                node=stack.pop();value=p['values'][node]
                if previous is not None and value<=previous:raise ValueError('notstrictBST')
                previous=value;node=p['right'][node]
        if pid==230 and not integer(args[1],1,n):raise ValueError('k')
        if pid in (235,236) and (len(set(p['values']))!=n or not integer(args[1],0,n-1) or not integer(args[2],0,n-1) or args[1]==args[2]):raise ValueError('actualdistinctp/qpoolidentities')
    elif pid in (234,237):
        cap=100000 if pid==234 else 1000;lo=0 if pid==234 else -1000;hi=9 if pid==234 else 1000
        if type(p) is not dict or set(p)!={'values','next','head'} or type(p['values']) is not list or not(1 if pid==234 else 2)<=len(p['values'])<=cap or not all(integer(v,lo,hi) for v in p['values']):raise ValueError('listvalues')
        n=len(p['values'])
        if type(p['next']) is not list or len(p['next'])!=n or any(i is not None and not integer(i,0,n-1) for i in p['next']) or not integer(p['head'],0,n-1):raise ValueError('listedges')
        list_order(p)
        if pid==237 and (len(set(p['values']))!=n or not integer(args[1],0,n-1) or p['next'][args[1]] is None):raise ValueError('non-tailtargetnode')
    elif pid==233:
        if not integer(p,0,10**9):raise ValueError('digitonebound')
    else:
        ops,rows=args
        if type(ops) is not list or type(rows) is not list or not 1<=len(ops)<=101 or len(ops)!=len(rows) or ops[0]!='MyQueue' or rows[0]!=[]:raise ValueError('MyQueuetraceconstructor')
        size=0
        for name,row in zip(ops[1:],rows[1:]):
            if type(name) is not str or name not in ('push','pop','peek','empty') or type(row) is not list or len(row)!=(1 if name=='push' else 0):raise ValueError('queuemethod/arity')
            if name=='push':
                if not integer(row[0],1,9):raise ValueError('queuepush')
                size+=1
            elif name in ('pop','peek'):
                if not size:raise ValueError('emptyquery')
                size-=name=='pop'
validate_domain=validate

def expected(pid,args):
    validate(pid,args);p=args[0]
    if pid==226:return None if p['root'] is None else {'original_id':p['root'],'value':p['values'][p['root']]}
    if pid==230:return sorted(p['values'])[args[1]-1]
    if pid==232:
        queue=deque();result=[None]
        for name,row in zip(p[1:],args[1][1:]):
            if name=='push':queue.append(row[0]);value=None
            elif name=='pop':value=queue.popleft()
            elif name=='peek':value=queue[0]
            else:value=not queue
            result.append(value)
        return result
    if pid==233:
        # Digit DP counts weighted padded-decimal strings, not positional cycles.
        states={True:(1,0)}
        for c in str(p):
            following={}
            for tight,(ways,ones) in states.items():
                limit=int(c) if tight else 9
                for digit in range(limit+1):
                    key=tight and digit==limit;w,o=following.get(key,(0,0));following[key]=(w+ways,o+ones+(ways if digit==1 else 0))
            states=following
        return sum(ones for ways,ones in states.values())
    if pid==234:
        values=[p['values'][i] for i in list_order(p)];return values==values[::-1]
    if pid in (235,236):
        # Bottom-up subtree mark counts, independent of BST valuepath/parentmap.
        counts=[0]*len(p['values']);answer=None
        for i in reversed(tree_order(p)):
            counts[i]=int(i==args[1])+int(i==args[2])+sum(counts[j] for j in (p['left'][i],p['right'][i]) if j is not None)
            if counts[i]==2 and not any(counts[j]==2 for j in (p['left'][i],p['right'][i]) if j is not None):answer=i
        return {'original_id':answer,'value':p['values'][answer]}
    target=args[1];order=list_order(p);successor=p['next'][target];visible=[i for i in order if i!=successor];values=[p['values'][i] for i in order if i!=target]
    return {'return':None,'head':p['head'],'order':visible,'values':values}

def accepts_result(pid,args,result):return exact(result,expected(pid,args))

def effect_plan(pid,args):
    validate(pid,args)
    if pid in (232,233):return {'raw_args_immutable':True,'native_receiver_count':1 if pid==232 else None}
    p=args[0];tree=pid in (226,230,235,236)
    before=[{'value':v,'left':p['left'][i],'right':p['right'][i]} if tree else {'value':v,'next':p['next'][i]} for i,v in enumerate(p['values'])];after=[dict(row) for row in before]
    if pid==226:
        for row in after:row['left'],row['right']=row['right'],row['left']
    elif pid==237:
        target=args[1];successor=p['next'][target];after[target]={'value':p['values'][successor],'next':p['next'][successor]}
    roots=[p['root'],args[1],args[2]] if pid in (235,236) else [args[1]] if pid==237 else [p['root'] if tree else p['head']]
    root=expected(pid,args).get('original_id') if pid in (235,236) else p['root'] if pid==226 else None
    return {'before':before,'after':after,'argument_roots':roots,'fixture_roots':[p['head']] if pid==237 else[],'result_root':root,'result_order':expected(pid,args)['order'] if pid==237 else None,'raw_args_immutable':True,'237_effect_scope':'Selectedcopy-nextsourcecontract, notofficialbanonotherlegalshiftimplementations' if pid==237 else None}

def check_effects(pid,args,record):
    if not exact(record.get('args_before'),args) or not exact(record.get('args_after'),args):return False,'raw_input_effect'
    if pid in (232,233):return True,None
    plan=effect_plan(pid,args);identity=record.get('node_identity')
    if type(identity) is not dict:return False,'node_identity'
    for key in ('before','after','argument_roots','fixture_roots','result_root','result_order'):
        if not exact(identity.get(key),plan[key]):return False,'native_effect_'+key
    return True,None

def check_observation(pid,args,record,language):
    """Semantic/effectmodel only; actualofficial/source/integrity needs Tbridge."""
    if not accepts_result(pid,args,record.get('result')):return False,'wrong_answer'
    return check_effects(pid,args,record)
