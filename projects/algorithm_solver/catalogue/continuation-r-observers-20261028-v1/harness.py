"""R original Python official classes/methods; no expected values or injection."""
import json
import importlib.util
from pathlib import Path

_SPEC=importlib.util.spec_from_file_location('trusted_r_native_graphs_v1',Path(__file__).with_name('native_graphs.py'))
_GRAPHS=importlib.util.module_from_spec(_SPEC);_SPEC.loader.exec_module(_GRAPHS)
Graph,build_list,build_shared,build_tree,class_guard=(_GRAPHS.Graph,_GRAPHS.build_list,_GRAPHS.build_shared,_GRAPHS.build_tree,_GRAPHS.class_guard)

IDS=(146,147,155,160,173,188)
CLASSES={146:('LRUCache',{'get':1,'put':2},{'put'}),155:('MinStack',{'push':1,'pop':0,'top':0,'getMin':0},{'push','pop'}),173:('BSTIterator',{'next':0,'hasNext':0},set())}
METHODS={147:'insertionSortList',160:'getIntersectionNode',188:'maxProfit'}
SEEN_RECEIVERS=[]

def fresh(receiver):
    if any(old is receiver for old in SEEN_RECEIVERS):raise TypeError('native receiver reused across traces')
    # Main accepts at most33 calls, bounding retained original receivers while
    # supporting source classes with slots/no weak-reference support.
    SEEN_RECEIVERS.append(receiver)


def clone(x):return json.loads(json.dumps(x,allow_nan=False,separators=(',',':')))


def observe(namespace,pid,call):
    if type(pid) is not int or pid not in IDS or type(call) is not dict or set(call)!={'args'} or type(call['args']) is not list:raise ValueError('fixed R argument-only call')
    args=clone(call['args']);before=clone(args)
    record={'native_route':'official-r-v1','problem_id':pid,'result':None,'result_type':None,'args_before':before,'args_after':None,'alias_edges':[],
            'node_identity':None,'node_integrity':None,'native_class':None,'native_receiver_count':None,'native_method_return_types':None,'native_method_snapshots':None,'method':None}
    graph=None;roots=[];initial=[];result_root=None
    if pid in CLASSES:
        name,methods,void=CLASSES[pid]
        if len(args)!=2 or type(args[0]) is not list or type(args[1]) is not list or len(args[0])!=len(args[1]) or not args[0] or args[0][0]!=name or any(type(r) is not list for r in args[1]):raise ValueError('one named constructor trace')
        operations,rows=args
        if len(operations)-1>{146:200000,155:30000,173:100000}[pid]:raise ValueError('official method count')
        ctor_args=rows[0]
        if pid==173:
            if len(ctor_args)!=1:raise ValueError('BSTIterator constructor arity')
            graph=Graph(namespace.get('TreeNode'),'tree',100000);root=build_tree(graph,ctor_args[0]);roots=[graph.identify(root)];initial=graph.snapshot();ctor_args=[root]
        elif len(ctor_args)!=(1 if pid==146 else 0):raise ValueError('class constructor arity')
        cls=namespace.get(name);guard=class_guard(cls)
        original_methods={method:vars(cls).get(method) for method in methods}
        if any(not callable(fn) for fn in original_methods.values()):raise TypeError('original declared class methods required')
        receiver=cls(*ctor_args)
        if type(receiver) is not cls:raise TypeError('original class instance required')
        fresh(receiver);guard()
        outputs=[None];types=['constructed'];snapshots=[None]
        for method,row in zip(operations[1:],rows[1:]):
            if type(method) is not str or method not in methods or len(row)!=methods[method]:raise ValueError('exact native method and arity')
            fn=original_methods[method]
            if not callable(fn):raise TypeError('original declared class method required')
            value=fn(receiver,*row)
            if type(receiver) is not cls:raise TypeError('original receiver class changed')
            if method in void and value is not None:raise TypeError('official void returns None')
            if method not in void and type(value) is not (bool if pid==173 and method=='hasNext' else int):raise TypeError('exact official primitive return type')
            outputs.append(value);types.append(type(value).__name__);snapshots.append(value)
        guard();record.update(result=outputs,result_type='list',native_class=name,native_receiver_count=1,native_method_return_types=types,native_method_snapshots=snapshots)
    else:
        method=METHODS[pid];record['method']=method
        cls=namespace.get('Solution');guard=class_guard(cls);receiver=cls()
        if type(receiver) is not cls:raise TypeError('original Solution receiver')
        fresh(receiver);guard()
        fn=vars(cls).get(method)
        if not callable(fn):raise TypeError('original official Solution method; no solve fallback')
        if pid==147:
            if len(args)!=1:raise ValueError('147 one native head')
            graph=Graph(namespace.get('ListNode'),'list',5000);heads=[build_list(graph,args[0])];roots=[graph.identify(heads[0])];initial=graph.snapshot();native_args=heads
        elif pid==160:
            if len(args)!=1:raise ValueError('160 one graph projects exactly two heads')
            graph=Graph(namespace.get('ListNode'),'list',60000);heads=build_shared(graph,args[0]);roots=[graph.identify(n) for n in heads];initial=graph.snapshot();native_args=heads
        else:
            if len(args)!=2:raise ValueError('188 k andprices')
            native_args=args
        value=fn(receiver,*native_args);guard();record['result_type']=type(value).__name__
        if graph:
            result_root=graph.identify(value);record['result']=graph.linked(value)
            if pid==147:record['args_after']=[graph.linked(heads[0])]
        else:
            if type(value) is not int:raise TypeError('188 exact integer profit')
            record['result']=clone(value)
    if graph:
        after=graph.snapshot();graph.guard()
        if len(after)!=len(initial):raise ValueError('replacement or extra reachable native nodes forbidden')
        if pid in (160,173) and after!=initial:raise ValueError('original native structure changed')
        if pid==147:
            if any(a['value']!=b['value'] for a,b in zip(after,initial)):raise ValueError('147 original values changed')
            seen=set();i=result_root
            while i is not None:
                if i in seen:raise ValueError('result cycle')
                seen.add(i);i=after[i]['next']
            if seen!=set(range(len(initial))):raise ValueError('147 must return everyoriginalnode')
        if pid==160:
            record['args_after']=clone(before)
            if value is None:record['result']=None
        elif pid==173:record['args_after']=clone(before)
        record['node_identity']={'before':initial,'after':after,'argument_roots':roots,'result_root':result_root}
        record['node_integrity']={'schema':'gamma.r-native-integrity.v1','class_or_prototype_unchanged':True,'own_field_descriptors_unchanged':True,'original_node_classes_unchanged':True,'acyclic_graphs':True,'checked_node_count':len(after),'native_aliases_in_identity_table':True}
        if result_root is not None:
            record['alias_edges']=[['result',f'args.{index}'] for index,r in enumerate(roots) if r==result_root]
    if record['args_after'] is None:record['args_after']=clone(args)
    return record


def main():
    with open('inputs.json') as f:packet=json.load(f)
    if type(packet) is not dict or set(packet)!={'schema','problem_id','calls'} or packet['schema']!='gamma.r-official-packet.v1' or type(packet['problem_id']) is not int or packet['problem_id'] not in IDS or type(packet['calls']) is not list or not 1<=len(packet['calls'])<=33:raise ValueError('fixed R native packet')
    namespace={'__name__':'candidate'}
    with open('program.py') as f:raw=f.read()
    exec(compile(raw,'program.py','exec'),namespace)
    for i,call in enumerate(packet['calls']):
        try:record={'i':i,**observe(namespace,packet['problem_id'],call)}
        except Exception as error:record={'i':i,'error':type(error).__name__+': '+str(error)[:300]}
        print(json.dumps(record,allow_nan=False,separators=(',',':')))
    print(json.dumps({'done':len(packet['calls'])}))

if __name__=='__main__':main()
