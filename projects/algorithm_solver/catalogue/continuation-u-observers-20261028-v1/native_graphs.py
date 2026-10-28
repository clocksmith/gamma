"""T original-constructor indexed models. No candidate loader or expected values."""
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
    def __init__(self,cls,kind,limit,required=False):
        self.cls=cls;self.guard=class_guard(cls);self.kind=kind;self.limit=limit
        self.fields=('val','next') if kind=='list' else ('val','left','right')
        self.nodes=[];self.ids={};self.external={}
        probe=cls(0) if required else cls();self.guard();data=self.data(probe)
        if data['val']!=0 or any(data[k] is not None for k in self.fields[1:]):raise ValueError('exact original constructor defaults')
    def data(self,node):
        if type(node) is not self.cls:raise TypeError('original source node class required')
        data=object.__getattribute__(node,'__dict__')
        if type(data) is not dict or set(data)!=set(self.fields) or type(data['val']) is not int:raise TypeError('exact own native node data fields')
        return data
    def construct(self,value):
        if type(value) is not int:raise TypeError('integer node value')
        node=self.cls(value);self.guard();data=self.data(node)
        if id(node) in self.ids or data['val']!=value or any(data[k] is not None for k in self.fields[1:]):raise ValueError('fresh original constructor defaults')
        if len(self.nodes)>=self.limit:raise ValueError('native node envelope')
        self.ids[id(node)]=len(self.nodes);self.nodes.append(node);return node
    def identify(self,node,external=False):
        if node is None:return None
        self.data(node)
        if id(node) in self.ids:return self.ids[id(node)]
        if not external:raise ValueError('result must use original node identity')
        if id(node) not in self.external:self.external[id(node)]=len(self.external)
        return {'external_identity':self.external[id(node)]}
    def snapshot(self):
        self.guard();rows=[]
        for node in self.nodes:
            data=self.data(node);row={'value':data['val']}
            for field in self.fields[1:]:row[field]=self.identify(data[field],external=True)
            rows.append(row)
        return rows
    def linked(self,root):
        order=[];seen=set();node=root
        while node is not None:
            index=self.identify(node)
            if index in seen:raise ValueError('returned list cycle')
            seen.add(index);order.append(index);node=self.data(node)['next']
        return {'head':self.identify(root),'order':order,'values':[self.data(self.nodes[i])['val'] for i in order]}



def build(graph,pid,wire):
    if type(pid) is not int or pid!=257:raise ValueError("fixed U257 graph")
    tree=pid in (257,230,235,236);keys={'values','left','right','root'} if tree else {'values','next','head'}
    if type(wire) is not dict or set(wire)!=keys or type(wire['values']) is not list:raise ValueError('exact indexed T native model')
    values=wire['values'];n=len(values)
    minimum=1
    if not minimum<=n<=graph.limit:raise ValueError('native size bound')
    low,high=(-100,100) if pid==257 else (0,10000) if pid==230 else (-10**9,10**9) if pid in (235,236) else (0,9) if pid==234 else (-1000,1000)
    if any(type(v) is not int or not low<=v<=high for v in values):raise ValueError('native value bounds')
    if pid in (230,235,236,237) and len(set(values))!=n:raise ValueError('unique original values required')
    def valid(index):return index is None or type(index) is int and 0<=index<n
    edges=('left','right') if tree else ('next',);root=wire['root' if tree else 'head']
    if not valid(root) or (root is None)!=(n==0):raise ValueError('native root')
    for field in edges:
        if type(wire[field]) is not list or len(wire[field])!=n or any(not valid(v) for v in wire[field]):raise ValueError('native edge indices')
    seen=set();queue=[root] if root is not None else []
    for i in queue:
        if i in seen:raise ValueError('original cycle or alias')
        seen.add(i)
        queue.extend(wire[field][i] for field in edges if wire[field][i] is not None)
    if len(seen)!=n:raise ValueError('unreachable original nodes')
    if pid in (230,235):
        pending=[];current=root;previous=None
        while current is not None or pending:
            while current is not None:pending.append(current);current=wire['left'][current]
            current=pending.pop()
            if previous is not None and previous>=values[current]:raise ValueError('strict BST required')
            previous=values[current];current=wire['right'][current]
    nodes=[graph.construct(value) for value in values]
    for i,node in enumerate(nodes):
        data=graph.data(node)
        for field in edges:data[field]=None if wire[field][i] is None else nodes[wire[field][i]]
    return None if root is None else nodes[root]
