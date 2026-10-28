"""S original Python official methods/design classes; argument-only child packet."""
import importlib.util
import json
from pathlib import Path
import weakref
_SPEC=importlib.util.spec_from_file_location('s_fixed_native_graphs',Path(__file__).with_name('native_graphs.py'))
_g=importlib.util.module_from_spec(_SPEC);_SPEC.loader.exec_module(_g)
IDS=(199,203,206,208,211,212,214,222,224,225)
METHODS={199:'rightSideView',203:'removeElements',206:'reverseList',212:'findWords',214:'shortestPalindrome',222:'countNodes',224:'calculate'}
CLASSES={208:('Trie',{'insert':1,'search':1,'startsWith':1},{'insert'},30000),211:('WordDictionary',{'addWord':1,'search':1},{'addWord'},10000),225:('MyStack',{'push':1,'pop':0,'top':0,'empty':0},{'push'},100)}
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
    if type(pid) is not int or pid not in IDS or type(call) is not dict or set(call)!={'args'} or type(call['args']) is not list:raise ValueError('fixed S argument-only call')
    args=clone(call['args']);before_args=clone(args)
    record={'native_route':'official-s-v1','problem_id':pid,'method':None,'entry_kind':None,'result':None,'result_type':None,'args_before':before_args,'args_after':None,'alias_edges':[],
            'node_identity':None,'node_integrity':None,'entry_integrity':{'schema':'gamma.s-entry-integrity.v1','original_export_unchanged':True,'class_or_prototype_unchanged':True,'method_descriptor_unchanged':True,'fresh_receiver':True},'native_class':None,'native_receiver_count':None,'native_method_return_types':None,'native_method_snapshots':None}
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
            elif type(value) is not (bool if pid in (208,211) or method=='empty' else int):raise TypeError('exact native primitive return type')
            guard()
            if any(name in vars(receiver) for name in methods):raise TypeError('receiver shadows original class method')
            if namespace.get(name) is not cls:raise TypeError('native class export changed')
            outputs.append(value);types.append(type(value).__name__);snapshots.append(clone(value))
        record.update(entry_kind='python-native-class',result=outputs,result_type='list',native_class=name,native_receiver_count=1,native_method_return_types=types,native_method_snapshots=snapshots)
    else:
        arity=2 if pid in (203,212) else 1
        if len(args)!=arity:raise ValueError('official method arity')
        method=METHODS[pid];cls=namespace.get('Solution');guard=_g.class_guard(cls);receiver=cls();guard()
        if type(receiver) is not cls:raise TypeError('original Solution receiver')
        fresh(receiver);fn=vars(cls).get(method)
        if not callable(fn):raise TypeError('original own Solution method, no solve fallback')
        graph=None;root=None;initial=[];ctor=None;native_args=args
        if pid in (199,203,206,222):
            name='TreeNode' if pid in (199,222) else 'ListNode';ctor=namespace.get(name);graph=_g.Graph(ctor,'tree' if pid in (199,222) else 'list',{199:100,203:10000,206:5000,222:50000}[pid]);root=_g.build(graph,pid,args[0]);initial=graph.snapshot();native_args=[root]+args[1:]
        value=fn(receiver,*native_args);guard()
        if type(receiver) is not cls:raise TypeError('original Solution receiver class changed')
        if namespace.get('Solution') is not cls:raise TypeError('original Solution export changed')
        record.update(method=method,entry_kind='python-solution-method',result_type=type(value).__name__)
        if graph:
            graph.guard()
            if namespace.get(name) is not ctor:raise TypeError('original node constructor export changed')
            after=graph.snapshot();result_root=None;order=None
            if pid in (203,206):
                normalized=graph.linked(value);result_root=normalized['head'];order=normalized['order'];record['result']=normalized
                if result_root is not None:record['alias_edges']=[['result',f'args.0.pool.{result_root}']]
            else:record['result']=clone(value)
            graph.guard();after=graph.snapshot()
            record['node_identity']={'before':initial,'after':after,'argument_roots':[graph.identify(root)],'result_root':result_root,'result_order':order}
            record['node_integrity']={'schema':'gamma.s-native-integrity.v1','class_or_prototype_unchanged':True,'own_field_descriptors_unchanged':True,'original_node_classes_unchanged':True,'checked_node_count':len(graph.nodes),'native_aliases_in_identity_table':True}
        else:
            record['alias_edges']=aliases(args,value);record['result']=clone(value)
    record['args_after']=clone(args)
    return record

def main():
    packet=json.loads(Path('inputs.json').read_text())
    if type(packet) is not dict or set(packet)!={'schema','problem_id','calls'} or packet['schema']!='gamma.s-official-packet.v1' or type(packet['problem_id']) is not int or packet['problem_id'] not in IDS or type(packet['calls']) is not list or not 1<=len(packet['calls'])<=33:raise ValueError('fixed S official packet')
    namespace={'__name__':'candidate'};source=Path('program.py').read_text();exec(compile(source,'program.py','exec'),namespace)
    for index,call in enumerate(packet['calls']):
        try:record={'i':index,**observe(namespace,packet['problem_id'],call)}
        except Exception as error:record={'i':index,'error':type(error).__name__+': '+str(error)[:300]}
        print(json.dumps(record,allow_nan=False,separators=(',',':')))
    print(json.dumps({'done':len(packet['calls'])}))
if __name__=='__main__':main()
