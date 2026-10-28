"""Original-source official P wrappers; no injected classes or expected answers."""
import json

METHODS={17:'letterCombinations',37:'solveSudoku',65:'isNumber',87:'isScramble',95:'generateTrees',99:'recoverTree',108:'sortedArrayToBST',114:'flatten',116:'connect',117:'connect'}
TREE={95,99,108,114,116,117}
VOID={37,99,114}
MAX_NODES=20000


def clone(value):
    return json.loads(json.dumps(value,allow_nan=False,separators=(',',':')))


def class_guard(cls):
    if type(cls) is not type:raise TypeError('original exported class required')
    chain=tuple((item,dict(vars(item))) for item in cls.__mro__)
    metadata=(cls.__mro__,cls.__name__,cls.__qualname__,cls.__bases__)
    def check():
        if (cls.__mro__,cls.__name__,cls.__qualname__,cls.__bases__)!=metadata:raise TypeError('original class metadata changed')
        for item,descriptors in chain:
            now=vars(item)
            if set(now)!=set(descriptors) or any(now[key] is not value for key,value in descriptors.items()):raise TypeError('original class descriptors changed')
    return check


class Graph:
    def __init__(self,cls,next_fields=False):
        self.cls=cls;self.guard=class_guard(cls);self.fields=('val','left','right','next') if next_fields else ('val','left','right')
        self.nodes=[];self.ids={}
    def data(self,node):
        if type(node) is not self.cls:raise TypeError('original source node class required')
        data=object.__getattribute__(node,'__dict__')
        if type(data) is not dict or set(data)!=set(self.fields):raise TypeError('original own node fields required')
        if type(data['val']) is not int:raise TypeError('exact integer node value required')
        return data
    def identify(self,node):
        if node is None:return None
        self.data(node)
        if id(node) not in self.ids:
            if len(self.nodes)>=MAX_NODES:raise ValueError('observer node envelope exceeded')
            self.ids[id(node)]=len(self.nodes);self.nodes.append(node)
        return self.ids[id(node)]
    def snapshot(self):
        self.guard();rows=[]
        for node in self.nodes:
            data=self.data(node);row={'id':self.ids[id(node)],'value':data['val']}
            for field in self.fields[1:]:row[field]=self.identify(data[field])
            rows.append(row)
        # Also inspect detached original nodes: no false integrity claim if
        # a candidate hides a cycle outside the final root traversal.
        colors={}
        for start in range(len(rows)):
            todo=[(start,False)]
            while todo:
                index,leaving=todo.pop()
                if leaving:colors[index]=2;continue
                if colors.get(index)==1:raise ValueError('detached or reachable node cycle')
                if colors.get(index)==2:continue
                colors[index]=1;todo.append((index,True))
                for field in ('right','left'):
                    child=rows[index][field]
                    if child is not None:todo.append((child,False))
        if 'next' in self.fields:
            done=set()
            for start in range(len(rows)):
                path=set();current=start
                while current is not None and current not in done:
                    if current in path:raise ValueError('next-pointer cycle')
                    path.add(current);current=rows[current]['next']
                done.update(path)
        return rows
    def tree(self,root,marker):
        if root is None:return {marker:[]}
        queue=[root];seen=set();values=[]
        for node in queue:
            if node is None:values.append(None);continue
            if id(node) in seen:raise ValueError('cycle or internal tree alias')
            seen.add(id(node));self.identify(node)
            if len(seen)>MAX_NODES:raise ValueError('tree envelope exceeded')
            data=self.data(node);values.append(data['val']);queue.extend((data['left'],data['right']))
        while values and values[-1] is None:values.pop()
        return {marker:values}


def build_tree(graph,wire,marker):
    if type(wire) is not dict or set(wire)!={marker} or type(wire[marker]) is not list:raise ValueError('exact tree marker required')
    values=wire[marker]
    if not values:return None
    if len(values)>2*MAX_NODES+1 or type(values[0]) is not int:raise ValueError('bounded nonnull tree root required')
    root=graph.cls(values[0]);queue=[root];index=1
    for parent in queue:
        for field in ('left','right'):
            if index>=len(values):break
            value=values[index];index+=1
            if value is not None:
                if type(value) is not int:raise TypeError('exact integer node value required')
                child=graph.cls(value);graph.data(parent)[field]=child;queue.append(child)
        if len(queue)>MAX_NODES:raise ValueError('input tree envelope exceeded')
    if index!=len(values):raise ValueError('unreachable tree slots')
    # Exact source defaults must provide null next pointers.
    if 'next' in graph.fields and any(graph.data(node)['next'] is not None for node in queue):raise ValueError('initial next pointers must be null')
    graph.tree(root,marker)
    return root


def observe(namespace,pid,call):
    if type(pid) is not int or pid not in METHODS or type(call) is not dict or set(call)!={'args'} or type(call['args']) is not list:raise ValueError('fixed argument-only official wrapper call required')
    if len(call['args'])!=(2 if pid==87 else 1):raise ValueError('exact official argument arity required')
    args=clone(call['args']);before=clone(args);solution=namespace.get('Solution');solution_guard=class_guard(solution)
    method=vars(solution).get(METHODS[pid])
    if not callable(method):raise TypeError('original official method required; no solve fallback')
    graph=None;root=None;argument_roots=[];before_nodes=[];marker='__next_node__' if pid in (116,117) else '__tree_node__'
    if pid in TREE:
        cls=namespace.get('Node' if pid in (116,117) else 'TreeNode');graph=Graph(cls,pid in (116,117))
        if pid in (99,114,116,117):
            if len(args)!=1:raise ValueError('one original tree argument required')
            root=build_tree(graph,args[0],marker);args=[root];argument_roots=[graph.identify(root)];before_nodes=graph.snapshot()
    receiver=solution()
    if type(receiver) is not solution:raise TypeError('original Solution receiver required')
    board=args[0] if pid==37 else None
    result=method(receiver,*args);solution_guard()
    if pid in VOID and result is not None:raise TypeError('official void method must return None')
    record={'native_route':'official-wrapper-p-v1','problem_id':pid,'method':METHODS[pid],
            'result':None,'result_type':type(result).__name__,'args_before':before,'args_after':None,'alias_edges':[],
            'node_identity':None,'node_integrity':None,'board_identity':None}
    if graph is None:
        record['result']=clone(result);record['args_after']=clone(args)
        if pid==37:
            if args[0] is not board:raise ValueError('original board argument root replaced')
            if type(board) is not list or len(board)!=9 or any(type(row) is not list or len(row)!=9 for row in board):raise ValueError('board shape changed')
            record['board_identity']={'argument_root_preserved':True,'before_shape':[9,9],'after_shape':[9,9]}
        return record
    result_root=None;result_roots=[]
    if pid==95:
        if type(result) is not list or len(result)>2000:raise TypeError('bounded actual node forest required')
        record['result']=[graph.tree(node,marker) for node in result];result_roots=[graph.identify(node) for node in result]
        record['args_after']=clone(args)
    elif pid==108:
        record['result']=graph.tree(result,marker);result_root=graph.identify(result);record['args_after']=clone(args)
    else:
        record['args_after']=[graph.tree(root,marker)]
        if pid in (116,117):
            if result is not root:raise ValueError('connect must return original root')
            record['result']=graph.tree(result,marker);result_root=graph.identify(result)
            if root is not None:record['alias_edges']=[['result','args.0']]
    after=graph.snapshot();graph.guard()
    record['node_identity']={'before':before_nodes,'after':after,'argument_roots':argument_roots,'result_root':result_root,'result_roots':result_roots}
    record['node_integrity']={'schema':'gamma.p-official-node-integrity.v1','class_or_prototype_unchanged':True,'own_field_descriptors_unchanged':True,'original_node_classes_unchanged':True,'acyclic_tree_graphs':True,'forest_cross_tree_aliases_permitted':pid==95,'checked_node_count':len(graph.nodes)}
    return record


def main():
    with open('inputs.json') as stream:packet=json.load(stream)
    if (type(packet) is not dict or set(packet)!={'schema','problem_id','calls'} or packet['schema']!='gamma.p-official-wrapper-packet.v1' or type(packet['problem_id']) is not int or packet['problem_id'] not in METHODS or type(packet['calls']) is not list):raise ValueError('fixed P official packet required')
    namespace={'__name__':'candidate'}
    with open('program.py') as stream:source=stream.read()
    exec(compile(source,'program.py','exec'),namespace)
    for index,call in enumerate(packet['calls']):
        try:record={'i':index,**observe(namespace,packet['problem_id'],call)}
        except Exception as error:record={'i':index,'error':type(error).__name__+': '+str(error)[:300]}
        print(json.dumps(record,allow_nan=False,separators=(',',':')))
    print(json.dumps({'done':len(packet['calls'])}))

if __name__=='__main__':main()
