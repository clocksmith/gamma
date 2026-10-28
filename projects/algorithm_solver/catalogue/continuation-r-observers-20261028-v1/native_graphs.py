"""R-v1 source-defined native graph guards; separate from prior P profiles."""

def class_guard(cls):
    if type(cls) is not type:raise TypeError('original source class required')
    chain=tuple((c,dict(vars(c))) for c in cls.__mro__);metadata=(type(cls),cls.__mro__,cls.__name__,cls.__qualname__,cls.__bases__)
    def check():
        if (type(cls),cls.__mro__,cls.__name__,cls.__qualname__,cls.__bases__)!=metadata:raise TypeError('class metadata changed')
        for c,fields in chain:
            now=vars(c)
            if set(now)!=set(fields) or any(now[k] is not v for k,v in fields.items()):raise TypeError('class descriptors changed')
    return check


class Graph:
    def __init__(self,cls,kind,limit):
        self.cls=cls;self.guard=class_guard(cls);self.kind=kind;self.limit=limit;self.fields=('val','next') if kind=='list' else ('val','left','right');self.nodes=[];self.ids={}
    def data(self,node):
        if type(node) is not self.cls:raise TypeError('original source node class required')
        data=object.__getattribute__(node,'__dict__')
        if type(data) is not dict or set(data)!=set(self.fields) or type(data['val']) is not int:raise TypeError('exact own native data fields required')
        return data
    def identify(self,node):
        if node is None:return None
        self.data(node)
        if id(node) not in self.ids:
            if len(self.nodes)>=self.limit:raise ValueError('fixed native representation limit')
            self.ids[id(node)]=len(self.nodes);self.nodes.append(node)
        return self.ids[id(node)]
    def construct(self,value):
        if type(value) is not int:raise TypeError('strict integer constructor value')
        node=self.cls(value);data=self.data(node)
        if data['val']!=value or any(data[k] is not None for k in self.fields[1:]):raise ValueError('original constructor defaults required')
        self.identify(node);return node
    def snapshot(self):
        self.guard();rows=[]
        for node in self.nodes:
            data=self.data(node);row={'id':self.ids[id(node)],'value':data['val']}
            for k in self.fields[1:]:row[k]=self.identify(data[k])
            rows.append(row)
        # Functional list/shared-tail graphs may alias between roots but never
        # cycle; trees may not cycle, including detached original nodes.
        colors={}
        for start in range(len(rows)):
            todo=[(start,False)]
            while todo:
                i,leave=todo.pop()
                if leave:colors[i]=2;continue
                if colors.get(i)==1:raise ValueError('native cycle')
                if colors.get(i)==2:continue
                colors[i]=1;todo.append((i,True))
                for k in self.fields[1:]:
                    if rows[i][k] is not None:todo.append((rows[i][k],False))
        return rows
    def linked(self,root):
        result=[];seen=set();node=root
        while node is not None:
            if id(node) in seen:raise ValueError('list cycle')
            seen.add(id(node));self.identify(node);data=self.data(node);result.append(data['val']);node=data['next']
        return {'__list_node__':result}
    def tree(self,root):
        result=[];seen=set();queue=[root] if root is not None else []
        for node in queue:
            if node is None:result.append(None);continue
            if id(node) in seen:raise ValueError('tree cycle or internal alias')
            seen.add(id(node));self.identify(node);data=self.data(node);result.append(data['val']);queue.extend((data['left'],data['right']))
        while result and result[-1] is None:result.pop()
        return {'__tree_node__':result}


def build_list(graph,wire):
    if type(wire) is not dict or set(wire)!={'__list_node__'} or type(wire['__list_node__']) is not list or not 1<=len(wire['__list_node__'])<=5000:raise ValueError('fixed147 list marker')
    nodes=[graph.construct(v) for v in wire['__list_node__']]
    if any(not -5000<=graph.data(n)['val']<=5000 for n in nodes):raise ValueError('147 values')
    for a,b in zip(nodes,nodes[1:]):graph.data(a)['next']=b
    return nodes[0]


def build_shared(graph,wire):
    if type(wire) is not dict or set(wire)!={'__list_graph__'}:raise ValueError('fixed160 shared graph marker')
    value=wire['__list_graph__']
    if type(value) is not dict or set(value)!={'nodes','argument_roots'} or type(value['nodes']) is not list or not 1<=len(value['nodes'])<=60000:raise ValueError('160 graph fields')
    rows=value['nodes'];roots=value['argument_roots']
    if type(roots) is not list or len(roots)!=2 or any(type(r) is not int or not 0<=r<len(rows) for r in roots):raise ValueError('two original nonnull heads')
    for row in rows:
        if type(row) is not dict or set(row)!={'value','next'} or type(row['value']) is not int or not 1<=row['value']<=100000 or row['next'] is not None and (type(row['next']) is not int or not 0<=row['next']<len(rows)):raise ValueError('160 original node fields')
    nodes=[graph.construct(row['value']) for row in rows]
    for node,row in zip(nodes,rows):graph.data(node)['next']=nodes[row['next']] if row['next'] is not None else None
    seen=set()
    for root in roots:
        graph.linked(nodes[root]);local=set();i=root
        while i is not None:
            local.add(i);seen.add(i);i=rows[i]['next']
        if len(local)>30000:raise ValueError('160 original list length')
    if seen!=set(range(len(rows))):raise ValueError('unreachable160 wire nodes')
    return [nodes[r] for r in roots]


def build_tree(graph,wire):
    if type(wire) is not dict or set(wire)!={'__tree_node__'} or type(wire['__tree_node__']) is not list:raise ValueError('173 constructor native tree')
    values=wire['__tree_node__']
    if not values or len(values)>200001:raise ValueError('173 nonempty bounded tree')
    root=graph.construct(values[0]);queue=[root];cursor=1
    for node in queue:
        for side in ('left','right'):
            if cursor>=len(values):continue
            v=values[cursor];cursor+=1
            if v is not None:
                child=graph.construct(v);graph.data(node)[side]=child;queue.append(child)
    if cursor!=len(values) or any(not 0<=graph.data(n)['val']<=1000000 for n in graph.nodes):raise ValueError('173 tree bounds')
    graph.tree(root);return root
