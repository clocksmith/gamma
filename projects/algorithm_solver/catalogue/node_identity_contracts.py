"""Exact original-node effect plans derived solely from admitted inputs."""
from copy import deepcopy
from math import gcd

IDS={814,2074,2807}


def original_nodes(argument):
    if '__list_node__' in argument:
        values=argument['__list_node__']
        return [{'value':v,'next':i+1 if i+1<len(values)else None}for i,v in enumerate(values)]
    values=argument['__tree_node__'];nodes=[{'value':values[0]}];cursor=1
    for node in nodes:
        for side in ('left','right'):
            value=values[cursor]if cursor<len(values)else None;cursor+=1
            node[side]=None if value is None else len(nodes)
            if value is not None:nodes.append({'value':value})
    return nodes


def serialize(nodes,root):
    if root is None:return None
    if 'next'in nodes[root]:
        values=[];seen=set();i=root
        while i is not None:
            if i in seen:raise ValueError('cycle')
            seen.add(i);values.append(nodes[i]['value']);i=nodes[i]['next']
        return {'__list_node__':values}
    values=[];queue=[root];seen=set()
    for i in queue:
        if i is None:values.append(None);continue
        if i in seen:raise ValueError('cycle')
        seen.add(i);values.append(nodes[i]['value']);queue.extend((nodes[i]['left'],nodes[i]['right']))
    while values and values[-1]is None:values.pop()
    return {'__tree_node__':values}


def plan(pid,args):
    before=original_nodes(args[0]);after=deepcopy(before);n=len(before);root=0
    if pid==814:
        keep=[False]*n
        for i in range(n-1,-1,-1):
            for side in ('left','right'):
                child=before[i][side]
                if child is not None and not keep[child]:after[i][side]=None
            keep[i]=bool(before[i]['value']or after[i]['left']is not None or after[i]['right']is not None)
        root=0 if keep[0]else None
    elif pid==2074:
        order=[];start=0;size=1
        while start<n:
            group=list(range(start,min(n,start+size)))
            order.extend(reversed(group)if len(group)%2==0 else group);start+=len(group);size+=1
        for position,i in enumerate(order):after[i]['next']=order[position+1]if position+1<n else None
    elif pid==2807:
        for i in range(n-1):
            after[i]['next']=n+i
            after.append({'value':gcd(before[i]['value'],before[i+1]['value']),'next':i+1})
    else:raise ValueError('unsupported node effect contract')
    return {'before':before,'after':after,'argument_roots':[0],'result_root':root}


def check(pid,args,record,equal,canonical):
    expected=plan(pid,args)
    if not equal(record.get('node_identity'),expected):return 'node_identity_effects'
    if not equal(record.get('args_before'),canonical(args)):return 'input_effects'
    if not equal(record.get('args_after'),[serialize(expected['after'],0)]):return 'input_effects'
    aliases=[['result','args.0']]if expected['result_root']is not None else []
    if not equal(record.get('alias_edges'),aliases):return 'return_aliases'
    return None
