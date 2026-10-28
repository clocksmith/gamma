"""Q original Python Solution methods with indexed native identity evidence."""
import json
import importlib.util
from pathlib import Path
_SPEC=importlib.util.spec_from_file_location('q_original_identity_primitives',Path(__file__).with_name('models.py'))
models=importlib.util.module_from_spec(_SPEC);_SPEC.loader.exec_module(models)

METHODS={126:'findLadders',129:'sumNumbers',132:'minCut',133:'cloneGraph',138:'copyRandomList',140:'wordBreak',141:'hasCycle',142:'detectCycle',143:'reorderList',144:'preorderTraversal'}
NATIVE={129,133,138,141,142,143,144}
LIMITS={129:1000,133:100,138:1000,141:10000,142:10000,143:50000,144:100}


def clone(value):return json.loads(json.dumps(value,allow_nan=False,separators=(',',':')))


def class_guard(cls):
    if type(cls) is not type:raise TypeError('original source class required')
    chain=tuple((item,dict(vars(item))) for item in cls.__mro__);metadata=(cls.__mro__,cls.__name__,cls.__qualname__,cls.__bases__)
    def check():
        if (cls.__mro__,cls.__name__,cls.__qualname__,cls.__bases__)!=metadata:raise TypeError('class metadata changed')
        for item,old in chain:
            now=vars(item)
            if set(now)!=set(old) or any(now[key] is not value for key,value in old.items()):raise TypeError('original class descriptors changed')
    return check


def fields(pid):return ('val','left','right') if pid in (129,144) else ('val','neighbors') if pid==133 else ('val','next','random') if pid==138 else ('val','next')


def inspect_pool(pid,pool,cls):
    for node in pool:
        if type(node) is not cls:raise TypeError('original exported node class required')
        data=object.__getattribute__(node,'__dict__')
        if type(data) is not dict or set(data)!=set(fields(pid)) or type(data['val']) is not int:raise TypeError('exact original own node fields required')
        if pid==133 and type(data['neighbors']) is not list:raise TypeError('actual neighbor list required')


def guarded_clone_pool(pid,result,originals,cls):
    if result is None:return models.clone_pool(pid,result,originals)
    inputs={id(node) for node in originals};seen=set();pool=[];pending=[result]
    for node in pending:
        if id(node) in inputs:raise ValueError('clone aliases input identity')
        if id(node) in seen:continue
        inspect_pool(pid,[node],cls);seen.add(id(node));pool.append(node)
        if len(pool)>len(originals):raise ValueError('clone count envelope')
        data=object.__getattribute__(node,'__dict__')
        following=data['neighbors'] if pid==133 else (data['next'],data['random'])
        pending.extend(child for child in following if child is not None)
    verified=models.clone_pool(pid,result,originals)
    if len(verified)!=len(pool) or any(a is not b for a,b in zip(verified,pool)):raise ValueError('clone traversal changed')
    return pool


def linear_reordered(head,pool,result):
    """Same contract as existing models.reordered, linear identity lookup."""
    if result is not None:raise TypeError('official reorderList must return None')
    index={id(node):i for i,node in enumerate(pool)};seen=set();order=[];node=head
    while node is not None:
        if id(node) not in index or id(node) in seen:raise ValueError('new node or cycle in reordered list')
        seen.add(id(node));order.append(index[id(node)]);node=node.next
    if len(order)!=len(pool):raise ValueError('lost original nodes')
    return {'return':None,'original_identity_order':order,'values':[pool[i].val for i in order]}


def aliases(args,result):
    originals={};todo=[(value,f'args.{i}') for i,value in enumerate(args)];seen=set()
    while todo:
        value,path=todo.pop()
        if type(value) not in (list,dict) or id(value) in seen:continue
        seen.add(id(value));originals[id(value)]=path
        todo.extend((child,f'{path}.{key}') for key,child in (enumerate(value) if type(value) is list else value.items()))
    edges=[];todo=[(result,'result')];seen=set()
    while todo:
        value,path=todo.pop()
        if type(value) not in (list,dict) or id(value) in seen:continue
        seen.add(id(value))
        if id(value) in originals:edges.append([path,originals[id(value)]])
        todo.extend((child,f'{path}.{key}') for key,child in (enumerate(value) if type(value) is list else value.items()))
    return sorted(edges)


def validate_model(pid,packet):
    if type(packet) is not dict or type(packet.get('values')) is not list or len(packet['values'])>LIMITS[pid]:raise ValueError('bounded indexed native model required')
    n=len(packet['values'])
    if any(type(value) is not int for value in packet['values']):raise TypeError('integer native values required')
    def index(value,nullable=True):
        if nullable and value is None:return
        if type(value) is not int or not 0<=value<n:raise ValueError('native index bound')
    if pid in (129,144):
        if set(packet)!={'values','left','right','root'}:raise ValueError('tree model fields')
        index(packet['root'])
        for field in ('left','right'):
            if type(packet[field]) is not list or len(packet[field])!=n:raise ValueError('tree edge count')
            for value in packet[field]:index(value)
    elif pid==133:
        if set(packet)!={'values','neighbors','root'} or type(packet['neighbors']) is not list or len(packet['neighbors'])!=n:raise ValueError('graph model fields')
        index(packet['root'])
        for row in packet['neighbors']:
            if type(row) is not list or len(row)>n:raise ValueError('neighbor envelope')
            for value in row:index(value,False)
    elif pid==138:
        if set(packet)!={'values','random'} or type(packet['random']) is not list or len(packet['random'])!=n:raise ValueError('random model fields')
        for value in packet['random']:index(value)
    elif pid in (141,142):
        if set(packet)!={'values','pos'} or type(packet['pos']) is not int or not -1<=packet['pos']<n:raise ValueError('build-only pos bound')
    elif set(packet)!={'values'}:raise ValueError('list model fields')


def observe(namespace,pid,call):
    if type(pid) is not int or pid not in METHODS or type(call) is not dict or set(call)!={'args'} or type(call['args']) is not list:raise ValueError('fixed argument-only Q call required')
    if len(call['args'])!=(3 if pid==126 else 2 if pid==140 else 1):raise ValueError('exact official arity required')
    args=clone(call['args']);before_args=clone(args);solution=namespace.get('Solution');solution_guard=class_guard(solution)
    method=vars(solution).get(METHODS[pid])
    if not callable(method):raise TypeError('original official Solution method required; no solve fallback')
    pool=[];root=None;before=[];node_guard=None;cls=None;neighbor_containers=[]
    if pid in NATIVE:
        validate_model(pid,args[0]);name='TreeNode' if pid in (129,144) else 'Node' if pid in (133,138) else 'ListNode'
        cls=namespace.get(name);node_guard=class_guard(cls);root,pool=models.materialize(pid,args[0],cls);inspect_pool(pid,pool,cls);before=models.snapshot(pid,pool)
        if pid==133:neighbor_containers=[node.neighbors for node in pool]
        args=[root]
    receiver=solution()
    if type(receiver) is not solution:raise TypeError('fresh original Solution receiver required')
    result=method(receiver,*args);solution_guard()
    if namespace.get('Solution') is not solution:raise TypeError('original Solution export changed')
    record={'native_route':'official-wrapper-q-v1','entry_kind':'python-solution-method','problem_id':pid,'method':METHODS[pid],
            'result':None,'result_type':type(result).__name__,'args_before':before_args,'args_after':None,'alias_edges':[],
            'node_identity':None,'node_integrity':None}
    if pid not in NATIVE:
        record['alias_edges']=aliases(args,result);record['result']=clone(result);record['args_after']=clone(args);return record
    node_guard()
    if namespace.get(name) is not cls:raise TypeError('original node export changed')
    inspect_pool(pid,pool,cls);after=models.snapshot(pid,pool)
    if pid==133 and any(node.neighbors is not container for node,container in zip(pool,neighbor_containers)):raise ValueError('original neighbor container replaced')
    original_root=models.original_entry(root,pool);clones=[];clone_snapshot=[];result_index=None;reordered=None
    if pid in (133,138):
        clones=guarded_clone_pool(pid,result,pool,cls);inspect_pool(pid,clones,cls);clone_snapshot=models.snapshot(pid,clones)
        if pid==133:
            clone_containers=[node.neighbors for node in clones]
            if len({id(value) for value in clone_containers})!=len(clone_containers) or any(any(value is original for original in neighbor_containers) for value in clone_containers):raise ValueError('clone adjacency containers not deeply disjoint')
        record['result']={'__clone_pool__':clone_snapshot,'root':0 if clones else None}
    elif pid==142:
        result_index=models.original_entry(result,pool);record['result']=result_index
        if result_index is not None:record['alias_edges']=[['result',f'args.0.pool.{result_index}']]
    elif pid==143:
        reordered=linear_reordered(root,pool,result);record['result']=reordered
    else:record['result']=clone(result)
    node_guard();inspect_pool(pid,pool,cls);after=models.snapshot(pid,pool)
    if pid==133 and any(node.neighbors is not container for node,container in zip(pool,neighbor_containers)):raise ValueError('original neighbor container replaced')
    record['args_after']=[{'__native_pool__':after,'root':original_root}]
    record['node_identity']={'before':before,'after':after,'argument_root':original_root,'original_node_count':len(pool),
                             'result_original_index':result_index,'clone_pool':clone_snapshot,'clone_root':0 if clones else None,'reordered':reordered}
    record['node_integrity']={'schema':'gamma.q-native-identity-integrity.v1','class_or_prototype_unchanged':True,
                             'own_field_descriptors_unchanged':True,'original_node_classes_unchanged':True,
                             'clone_pool_disjoint':True if pid in (133,138) else None,
                             'original_neighbor_containers_unchanged':True if pid==133 else None}
    return record


def main():
    with open('inputs.json') as stream:packet=json.load(stream)
    if type(packet) is not dict or set(packet)!={'schema','problem_id','calls'} or packet['schema']!='gamma.q-official-wrapper-packet.v1' or type(packet['problem_id']) is not int or packet['problem_id'] not in METHODS or type(packet['calls']) is not list:raise ValueError('fixed Q official packet required')
    namespace={'__name__':'candidate'}
    with open('program.py') as stream:source=stream.read()
    exec(compile(source,'program.py','exec'),namespace)
    for index,call in enumerate(packet['calls']):
        try:record={'i':index,**observe(namespace,packet['problem_id'],call)}
        except Exception as error:record={'i':index,'error':type(error).__name__+': '+str(error)[:300]}
        print(json.dumps(record,allow_nan=False,separators=(',',':')))
    print(json.dumps({'done':len(packet['calls'])}))
if __name__=='__main__':main()
