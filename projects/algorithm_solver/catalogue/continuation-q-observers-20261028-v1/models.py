"""Source-free native model adapter primitives, no candidate loader/engine.
Factories must be original constructors exported by pinned candidate source.
An existing isolated observer must bind these primitives in a NEW Q profile.
"""
def materialize(pid,packet,factory):
    nodes=[factory(value) for value in packet['values']]
    if pid in (129,144):
        for i,node in enumerate(nodes):
            node.left=None if packet['left'][i] is None else nodes[packet['left'][i]]
            node.right=None if packet['right'][i] is None else nodes[packet['right'][i]]
        return (None if packet['root'] is None else nodes[packet['root']]),nodes
    if pid==133:
        for i,node in enumerate(nodes):node.neighbors=[nodes[j] for j in packet['neighbors'][i]]
        return (None if packet['root'] is None else nodes[packet['root']]),nodes
    for i,node in enumerate(nodes):node.next=nodes[i+1] if i+1<len(nodes) else nodes[packet['pos']] if pid in (141,142) and packet['pos']!=-1 else None
    if pid==138:
        for i,node in enumerate(nodes):node.random=None if packet['random'][i] is None else nodes[packet['random'][i]]
    return (nodes[0] if nodes else None),nodes

def snapshot(pid,nodes):
    index={id(node):i for i,node in enumerate(nodes)}
    if len(index)!=len(nodes):raise ValueError('duplicate original identity')
    def reference(node):
        if node is None:return None
        if id(node) not in index:raise ValueError('edge outside declared nodepool')
        return index[id(node)]
    fields=('left','right') if pid in (129,144) else ('neighbors',) if pid==133 else ('next','random') if pid==138 else ('next',)
    result=[]
    for node in nodes:
        if set(vars(node))!={'val',*fields}:raise ValueError('unexpected native fields')
        row={'value':node.val}
        for field in fields:
            value=getattr(node,field)
            if field=='neighbors':
                if type(value) is not list:raise ValueError('neighbor container')
                row[field]=[reference(v) for v in value]
            else:row[field]=reference(value)
        result.append(row)
    return result

def original_entry(result,nodes):
    if result is None:return None
    for i,node in enumerate(nodes):
        if result is node:return i
    raise ValueError('returned equal-valued clone instead of original identity')

def reordered(head,nodes,result):
    if result is not None:raise ValueError('reorderList must return void')
    order=[];seen=set();current=head
    while current is not None:
        index=original_entry(current,nodes)
        if index in seen:raise ValueError('cycle in reordered result')
        seen.add(index);order.append(index);current=current.next
    if len(order)!=len(nodes):raise ValueError('lost original nodes')
    return {'return':None,'original_identity_order':order,'values':[nodes[i].val for i in order]}

def clone_pool(pid,result,originals):
    if result is None:
        if originals:raise ValueError('missing clone root')
        return []
    input_ids={id(node) for node in originals};seen=set();pool=[];pending=[result]
    for node in pending:
        if id(node) in input_ids:raise ValueError('clone aliases input identity')
        if id(node) in seen:continue
        seen.add(id(node));pool.append(node)
        following=node.neighbors if pid==133 else [node.next,node.random]
        pending.extend(value for value in following if value is not None)
        if len(pool)>len(originals):raise ValueError('too many clone identities')
    if len(pool)!=len(originals):raise ValueError('clone nodecount mismatch')
    return pool
