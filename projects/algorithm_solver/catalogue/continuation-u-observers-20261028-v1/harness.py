"""U257 original Python Solution method and source TreeNode, no solver injection."""
import importlib.util
import json
from pathlib import Path
import weakref
_SPEC=importlib.util.spec_from_file_location('u_native_graphs',Path(__file__).with_name('native_graphs.py'))
g=importlib.util.module_from_spec(_SPEC);_SPEC.loader.exec_module(g)
SEEN=weakref.WeakValueDictionary()
def clone(x):return json.loads(json.dumps(x,allow_nan=False))
def observe(namespace,pid,call):
    if type(pid) is not int or pid!=257 or type(call) is not dict or set(call)!={'args'} or type(call['args']) is not list or len(call['args'])!=1:raise ValueError('fixed U257 argument-only call')
    args=clone(call['args']);before=clone(args);cls=namespace.get('Solution');guard=g.class_guard(cls);receiver=cls();guard()
    if type(receiver) is not cls or SEEN.get(id(receiver)) is receiver:raise TypeError('fresh original Solution receiver')
    SEEN[id(receiver)]=receiver
    fn=vars(cls).get('binaryTreePaths')
    if not callable(fn) or 'binaryTreePaths' in vars(receiver):raise TypeError('original own Solution method')
    ctor=namespace.get('TreeNode');graph=g.Graph(ctor,'tree',100);root=g.build(graph,pid,args[0]);initial=graph.snapshot()
    value=fn(receiver,root);guard();graph.guard()
    if type(receiver) is not cls or namespace.get('Solution') is not cls or namespace.get('TreeNode') is not ctor or 'binaryTreePaths' in vars(receiver):raise TypeError('original exports/receiver changed')
    if type(value) is not list or any(type(v) is not str for v in value):raise TypeError('exact list of strings required')
    return {'native_route':'official-u-v1','problem_id':pid,'method':'binaryTreePaths','entry_kind':'python-solution-method','result':clone(value),'result_type':'list','args_before':before,'args_after':clone(args),'alias_edges':[],
      'node_identity':{'before':initial,'after':graph.snapshot(),'argument_roots':[graph.identify(root)],'fixture_roots':[],'result_root':None,'result_order':None},
      'node_integrity':{'schema':'gamma.u-native-integrity.v1','class_or_prototype_unchanged':True,'own_field_descriptors_unchanged':True,'original_node_classes_unchanged':True,'checked_node_count':len(graph.nodes),'native_aliases_in_identity_table':True},
      'entry_integrity':{'schema':'gamma.u-entry-integrity.v1','original_export_unchanged':True,'class_or_prototype_unchanged':True,'method_descriptor_unchanged':True,'fresh_receiver':True}}
def main():
    p=json.loads(Path('inputs.json').read_text())
    if type(p) is not dict or set(p)!={'schema','problem_id','calls'} or p['schema']!='gamma.u-official-packet.v1' or type(p['problem_id']) is not int or p['problem_id']!=257 or type(p['calls']) is not list or not 1<=len(p['calls'])<=33:raise ValueError('fixed U257 packet')
    namespace={'__name__':'candidate'};exec(compile(Path('program.py').read_text(),'program.py','exec'),namespace)
    for i,call in enumerate(p['calls']):
        try:record={'i':i,**observe(namespace,p['problem_id'],call)}
        except Exception as e:record={'i':i,'error':type(e).__name__+': '+str(e)[:300]}
        print(json.dumps(record,allow_nan=False,separators=(',',':')))
    print(json.dumps({'done':len(p['calls'])}))
if __name__=='__main__':main()
