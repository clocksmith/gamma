"""T original Python official methods/design classes; argument-only child packet."""
import importlib.util
import json
from pathlib import Path
import weakref
_SPEC=importlib.util.spec_from_file_location('t_fixed_native_graphs',Path(__file__).with_name('native_graphs.py'))
_g=importlib.util.module_from_spec(_SPEC);_SPEC.loader.exec_module(_g)
IDS=(226,230,232,233,234,235,236,237)
METHODS={226:'invertTree',230:'kthSmallest',233:'countDigitOne',234:'isPalindrome',235:'lowestCommonAncestor',236:'lowestCommonAncestor',237:'deleteNode'}
CLASSES={232:('MyQueue',{'push':1,'pop':0,'peek':0,'empty':0},{'push'},100)}
SEEN=weakref.WeakValueDictionary()
def fresh(receiver):
    if SEEN.get(id(receiver)) is receiver:raise TypeError('original receiver reused across calls')
    SEEN[id(receiver)]=receiver

def clone(value):return json.loads(json.dumps(value,allow_nan=False,separators=(',',':')))

def aliases(args,result):
    originals={};pending=[(v,f'args.{i}') for i,v in enumerate(args)];seen=set()
    while pending:
        value,path=pending.pop()
        if type(value) not in (dict,list) or id(value) in seen:continue
        seen.add(id(value));originals[id(value)]=path
        pending.extend((v,f'{path}.{k}') for k,v in (value.items() if type(value) is dict else enumerate(value)))
    result_aliases=[];pending=[(result,'result')];seen=set()
    while pending:
        value,path=pending.pop()
        if type(value) not in (dict,list) or id(value) in seen:continue
        seen.add(id(value))
        if id(value) in originals:result_aliases.append([path,originals[id(value)]])
        pending.extend((v,f'{path}.{k}') for k,v in (value.items() if type(value) is dict else enumerate(value)))
    return sorted(result_aliases)

def observe(namespace,pid,call):
    if type(pid) is not int or pid not in IDS or type(call) is not dict or set(call)!={'args'} or type(call['args']) is not list:raise ValueError('fixed T argument-only call')
    args=clone(call['args']);before_args=clone(args)
    record={'native_route':'official-t-v1','problem_id':pid,'method':None,'entry_kind':None,'result':None,'result_type':None,'args_before':before_args,'args_after':None,'alias_edges':[],
            'node_identity':None,'node_integrity':None,'entry_integrity':{'schema':'gamma.t-entry-integrity.v1','original_export_unchanged':True,'class_or_prototype_unchanged':True,'method_descriptor_unchanged':True,'fresh_receiver':True},'native_class':None,'native_receiver_count':None,'native_method_return_types':None,'native_method_snapshots':None}
    if pid in CLASSES:
        name,methods,void,limit=CLASSES[pid]
        if len(args)!=2 or type(args[0]) is not list or type(args[1]) is not list or not args[0] or len(args[0])!=len(args[1]) or args[0][0]!=name or args[1][0]!=[] or len(args[0])-1>limit or any(type(row) is not list for row in args[1]):raise ValueError('one bounded native constructor trace')
        cls=namespace.get(name);guard=_g.class_guard(cls);receiver=cls();guard()
        if type(receiver) is not cls:raise TypeError('original design receiver class')
        fresh(receiver)
        if any(name in vars(receiver) for name in methods):raise TypeError('receiver shadows original class method')
        outputs=[None];types=['constructed'];snapshots=[None]
        for method,row in zip(args[0][1:],args[1][1:]):
            if type(method) is not str or method not in methods or len(row)!=methods[method]:raise ValueError('declared native method/arity')
            fn=vars(cls).get(method)
            if not callable(fn):raise TypeError('original own native class method required')
            value=fn(receiver,*row)
            if type(receiver) is not cls:raise TypeError('receiver class changed')
            if method in void:
                if value is not None:raise TypeError('official void returns None')
            elif type(value) is not (bool if method=='empty' else int):raise TypeError('exact native primitive return type')
            guard()
            if any(name in vars(receiver) for name in methods):raise TypeError('receiver shadows original class method')
            if namespace.get(name) is not cls:raise TypeError('native class export changed')
            outputs.append(value);types.append(type(value).__name__);snapshots.append(clone(value))
        record.update(entry_kind='python-native-class',result=outputs,result_type='list',native_class=name,native_receiver_count=1,native_method_return_types=types,native_method_snapshots=snapshots)
    else:
        arity=3 if pid in (235,236) else 2 if pid in (230,237) else 1
        if len(args)!=arity:raise ValueError('official method arity')
        method=METHODS[pid];cls=namespace.get('Solution');guard=_g.class_guard(cls);receiver=cls();guard()
        if type(receiver) is not cls:raise TypeError('original Solution receiver')
        fresh(receiver);fn=vars(cls).get(method)
        if not callable(fn):raise TypeError('original own Solution method, no solve fallback')
        graph=None;root=None;initial=[];ctor=None;native_args=args;argument_roots=[];fixture_roots=[]
        if pid!=233:
            name='TreeNode' if pid in (226,230,235,236) else 'ListNode';ctor=namespace.get(name)
            graph=_g.Graph(ctor,'tree' if pid in (226,230,235,236) else 'list',{226:100,230:10000,234:100000,235:100000,236:100000,237:1000}[pid],required=pid in (235,236,237))
            root=_g.build(graph,pid,args[0]);initial=graph.snapshot();argument_roots=[graph.identify(root)];native_args=[root]
            if pid==230:
                if type(args[1]) is not int or not 1<=args[1]<=len(graph.nodes):raise ValueError('k domain')
                native_args.append(args[1])
            elif pid in (235,236):
                p,q=args[1:]
                if any(type(i) is not int or not 0<=i<len(graph.nodes) for i in (p,q)) or p==q:raise ValueError('original distinct p/q identities')
                native_args.extend((graph.nodes[p],graph.nodes[q]));argument_roots.extend((p,q))
            elif pid==237:
                target=args[1]
                if type(target) is not int or not 0<=target<len(graph.nodes) or graph.data(graph.nodes[target])['next'] is None:raise ValueError('non-tail original target')
                fixture_roots=[graph.identify(root)];argument_roots=[target];native_args=[graph.nodes[target]]
        value=fn(receiver,*native_args);guard()
        if type(receiver) is not cls:raise TypeError('original Solution receiver class changed')
        if namespace.get('Solution') is not cls:raise TypeError('original Solution export changed')
        record.update(method=method,entry_kind='python-solution-method',result_type=type(value).__name__)
        if graph:
            graph.guard()
            if namespace.get(name) is not ctor:raise TypeError('original node constructor export changed')
            after=graph.snapshot();result_root=None;order=None
            if pid in (226,235,236):
                result_root=graph.identify(value)
                if pid in (235,236) and result_root is None:raise ValueError('LCA must be original existing node')
                record['result']=None if result_root is None else {'original_id':result_root,'value':graph.data(value)['val']}
                if result_root is not None:
                    record['alias_edges']=sorted([['result',f'args.0.pool.{result_root}']]+[['result',f'args.{i}'] for i,index in enumerate(argument_roots) if index==result_root])
            elif pid==237:
                if value is not None:raise TypeError('deleteNode must return None')
                visible=graph.linked(root);record['result']={'return':None,**visible};order=visible['order']
            else:record['result']=clone(value)
            graph.guard();after=graph.snapshot()
            record['node_identity']={'before':initial,'after':after,'argument_roots':argument_roots,'fixture_roots':fixture_roots,'result_root':result_root,'result_order':order}
            record['node_integrity']={'schema':'gamma.t-native-integrity.v1','class_or_prototype_unchanged':True,'own_field_descriptors_unchanged':True,'original_node_classes_unchanged':True,'checked_node_count':len(graph.nodes),'native_aliases_in_identity_table':True}
        else:
            record['alias_edges']=aliases(args,value);record['result']=clone(value)
    record['args_after']=clone(args)
    return record

def main():
    packet=json.loads(Path('inputs.json').read_text())
    if type(packet) is not dict or set(packet)!={'schema','problem_id','calls'} or packet['schema']!='gamma.t-official-packet.v1' or type(packet['problem_id']) is not int or packet['problem_id'] not in IDS or type(packet['calls']) is not list or not 1<=len(packet['calls'])<=33:raise ValueError('fixed T official packet')
    namespace={'__name__':'candidate'};source=Path('program.py').read_text();exec(compile(source,'program.py','exec'),namespace)
    for index,call in enumerate(packet['calls']):
        try:record={'i':index,**observe(namespace,packet['problem_id'],call)}
        except Exception as error:record={'i':index,'error':type(error).__name__+': '+str(error)[:300]}
        print(json.dumps(record,allow_nan=False,separators=(',',':')))
    print(json.dumps({'done':len(packet['calls'])}))
if __name__=='__main__':main()
