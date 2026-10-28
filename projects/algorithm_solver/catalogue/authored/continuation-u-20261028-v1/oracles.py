"""U independent serialized reference/effect models, no candidate implementation.
Only257 has a verified available full specification and both language templates.
A separate original-constructor native observer is required for ABI qualification.
"""
from collections import Counter,deque
REQUESTED_IDS=(246,247,248,249,250,254,255,256,257,259)
IDS=(257,)
BLOCKED_IDS=(246,247,248,249,250,254,255,256,259)
METHODS={257:'binaryTreePaths'}

def exact(a,b):
    if type(a) is not type(b):return False
    if type(a) is list:return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    if type(a) is dict:return set(a)==set(b) and all(exact(a[k],b[k]) for k in a)
    return a==b

def integer(value,lo,hi):return type(value) is int and lo<=value<=hi

def tree_model(packet):
    if type(packet) is not dict or set(packet)!={'values','left','right','root'}:raise ValueError('exact indexed tree model')
    values=packet['values']
    if type(values) is not list or not 1<=len(values)<=100 or not all(integer(v,-100,100) for v in values):raise ValueError('official tree values/count')
    n=len(values);root=packet['root']
    if not integer(root,0,n-1):raise ValueError('original nonnull root index')
    parent=[None]*n
    for field in ('left','right'):
        edges=packet[field]
        if type(edges) is not list or len(edges)!=n:raise ValueError('tree edge count')
        for original,child in enumerate(edges):
            if child is None:continue
            if not integer(child,0,n-1) or child==root or parent[child] is not None:raise ValueError('tree edge index or multiple parents')
            parent[child]=original
    seen=set();pending=[root]
    for node in pending:
        if node in seen:raise ValueError('tree cycle or repeated identity')
        seen.add(node);pending.extend(child for child in (packet['left'][node],packet['right'][node]) if child is not None)
    if len(seen)!=n:raise ValueError('disconnected original pool')
    return parent

def validate(pid,args):
    if type(pid) is not int or pid not in IDS:raise ValueError('U specification unavailable or identity not active')
    if type(args) is not list or len(args)!=1:raise ValueError('one indexed native root argument')
    tree_model(args[0])
validate_domain=validate

def expected(pid,args):
    validate(pid,args);packet=args[0];parent=tree_model(packet);paths=[]
    # Inspect leaves first and ascend parent links. No candidate-style rooted
    # recursive/iterative path traversal is reused in this reference.
    for leaf in range(len(parent)):
        if packet['left'][leaf] is not None or packet['right'][leaf] is not None:continue
        reversed_values=[];current=leaf
        while current is not None:
            reversed_values.append(packet['values'][current]);current=parent[current]
        paths.append('->'.join(str(value) for value in reversed(reversed_values)))
    return sorted(paths)

def accepts_result(pid,args,result):
    wanted=expected(pid,args)
    return type(result) is list and all(type(path) is str for path in result) and Counter(result)==Counter(wanted)

def effect_plan(pid,args):
    validate(pid,args);p=args[0];rows=[{'value':value,'left':p['left'][i],'right':p['right'][i]} for i,value in enumerate(p['values'])]
    return {'before':rows,'after':rows,'argument_roots':[p['root']],'fixture_roots':[],'result_root':None,'result_order':None,'raw_args_immutable':True,'readonly_original_pool':True,'output_order':'any','output_multiplicity':'one path per leaf identity; equal strings remain repeated'}

def check_effects(pid,args,record):
    if not exact(record.get('args_before'),args) or not exact(record.get('args_after'),args):return False,'raw_model_input_effect'
    plan=effect_plan(pid,args);identity=record.get('node_identity')
    if type(identity) is not dict or set(identity)!={'before','after','argument_roots','fixture_roots','result_root','result_order'}:return False,'node_identity_shape'
    for key in identity:
        if not exact(identity[key],plan[key]):return False,'original_tree_identity_or_field_effect'
    return True,None

def check_observation(pid,args,record,language):
    """Semantic/effect models ONLY; does not confer official native ABI proof."""
    if not accepts_result(pid,args,record.get('result')):return False,'wrong_path_multiset'
    return check_effects(pid,args,record)
