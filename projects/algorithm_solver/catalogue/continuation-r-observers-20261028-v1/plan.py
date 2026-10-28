"""Prospective R argument-only packets and conservative successful-output bounds.

No source bodies/runtime execution; blocked witnesses remain explicit.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'authored/continuation-r-20261028-v1'
REFERENCE_FREEZE_SHA='a8b230143769dc7b9c67196d033d30fe5532e02b88426ccfdce2e38a9d728031'
MAX_HOST_PACKET_BYTES=16*1024**2
MAX_OUTPUT_BYTES=16*1024**2
MAX_CALLS=33
POLICY='r-v1-small-first-repeat;large-repeat-or-small-large-small;retain-blocked'


def encoded(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()


def references():
    raw=(SOURCE/'pre-source-reference-freeze.json').read_bytes()
    if sha(raw)!=REFERENCE_FREEZE_SHA:raise ValueError('R independent pre-source freeze drift')
    freeze=json.loads(raw)
    for name,pin in freeze['files'].items():
        if sha((SOURCE/name).read_bytes())!=pin:raise ValueError('frozen source-free R owner drift')
    spec=importlib.util.spec_from_file_location('r_frozen_case_owner',SOURCE/'cases.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module,freeze


def packet(pid,rows,indices):return {'schema':'gamma.r-official-packet.v1','problem_id':pid,'calls':[{'args':rows[i]['args']} for i in indices]}


def successful_record(pid,args,want,language,oracle):
    r={'native_route':'official-r-v1','problem_id':pid,'result':want,'result_type':None,'args_before':args,'args_after':args,'alias_edges':[],
       'node_identity':None,'node_integrity':None,'native_class':None,'native_receiver_count':None,'native_method_return_types':None,'native_method_snapshots':None,'method':None}
    if pid in oracle.CLASSES:
        r.update(result_type='list' if language=='python' else 'object',native_class=oracle.CLASSES[pid],native_receiver_count=1,
                 native_method_return_types=oracle.class_return_types(pid,args,language),native_method_snapshots=want)
    else:r['method']=oracle.METHODS[pid]
    if pid==188:r['result_type']='int' if language=='python' else 'number'
    if pid in (147,160,173):
        root=None
        if pid==147:
            nodes=oracle.list_nodes(args[0]);roots=[0];order=sorted(range(len(nodes)),key=lambda i:nodes[i]['value']);root=order[0]
            after=[dict(row) for row in nodes]
            for pos,i in enumerate(order):after[i]['next']=order[pos+1] if pos+1<len(order) else None
            r['args_after']=[want] # All values upper-bound any original-head suffix.
            r['result_type']='ListNode' if language=='python' else 'object'
        elif pid==160:
            nodes,roots,_=oracle.shared_graph(args[0]);after=nodes;root=want
            values=[];i=root
            while i is not None:values.append(nodes[i]['value']);i=nodes[i]['next']
            r['result']=None if root is None else {'__list_node__':values}
            r['result_type']=('NoneType' if root is None else 'ListNode') if language=='python' else 'object'
        else:nodes=oracle.tree_nodes(args[1][0][0]);roots=[0];after=nodes
        r['node_identity']={'before':[{'id':i,**row} for i,row in enumerate(nodes)],'after':[{'id':i,**row} for i,row in enumerate(after)],'argument_roots':roots,'result_root':root}
        r['node_integrity']={'schema':'gamma.r-native-integrity.v1','class_or_prototype_unchanged':True,'own_field_descriptors_unchanged':True,'original_node_classes_unchanged':True,'acyclic_graphs':True,'checked_node_count':len(nodes),'native_aliases_in_identity_table':True}
        if root is not None:r['alias_edges']=[['result',f'args.{i}'] for i,v in enumerate(roots) if v==root]
    return r


def projection(pid,rows,language,oracle):
    result=[]
    for row in rows:
        record=successful_record(pid,row['args'],row['expected'],language,oracle)
        # i is packet-position dependent:20decimal digits plus128bytes cover
        # terminal spacing, root-alias spelling and bounded number formatting.
        #147ties can permute pointer-ID decimal widths;8bytes/node is a
        # conservative envelope, not a prediction of a chosen source ordering.
        size=len(encoded({'i':10**19,**record}))+1+128
        if pid==147:size+=8*len(row['args'][0]['__list_node__'])
        result.append(size)
    return result


def batch_plan(pid,rows,oracle):
    if not rows:raise ValueError('nonempty retained case suite')
    costs={lang:projection(pid,rows,lang,oracle) for lang in ('python','javascript')}
    sizes=[len(encoded(r['args'])) for r in rows]
    probe=min(range(len(rows)),key=lambda i:sizes[i]+max(costs[l][i] for l in costs))
    def measured(indices,mode):
        return {'indices':indices,'mode':mode,'host_input_bytes':len(encoded(packet(pid,rows,indices))),
                'projected_output_bytes':{lang:sum(costs[lang][i] for i in indices)+64 for lang in costs}}
    def fits(entry):return len(entry['indices'])<=MAX_CALLS and entry['host_input_bytes']<=MAX_HOST_PACKET_BYTES and max(entry['projected_output_bytes'].values())<=MAX_OUTPUT_BYTES
    batches=[];blocked=[];small=[];small_size=0
    def flush():
        nonlocal small,small_size
        if small:
            entry=measured(small+[small[0]],'small-first-call-repeat')
            if not fits(entry):raise ValueError('small-packet envelope calculation failed')
            batches.append(entry);small=[];small_size=0
    for i,size in enumerate(sizes):
        if size>256*1024 or max(costs[l][i] for l in costs)>256*1024:
            flush();options=[measured([i,i],'large-repeat'),measured([probe,i,probe],'small-large-small')]
            good=next((e for e in options if fits(e)),None)
            if good:batches.append(good)
            else:blocked.append({'case':i,'status':'blocked_transport','single':measured([i],'single-witness-bound'),'reason':'full original witness retained; no cap raise or silent omission'})
        else:
            if small and (len(small)>=32 or small_size+size>256*1024):flush()
            candidate=measured(small+[i]+[small[0] if small else i],'trial')
            if small and not fits(candidate):flush()
            small.append(i);small_size+=size
    flush()
    covered={i for e in batches for i in e['indices']};excluded={r['case'] for r in blocked}
    if covered&excluded or covered|excluded!=set(range(len(rows))):raise ValueError('case lost or double-classified')
    return {'policy':POLICY,'logical_cases':len(rows),'admitted_distinct_cases':len(covered),'batches':batches,'blocked_cases':blocked}
