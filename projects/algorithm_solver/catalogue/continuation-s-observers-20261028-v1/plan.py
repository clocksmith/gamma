"""Prospective S argument-only packet/output envelopes, no candidate/runtime work.
Uses the current R-lane16MiB host envelopes as planning ceilings only; execution
owner must confirm unchanged actual caps. Smaller-cap exclusions remain explicit.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'authored/continuation-s-20261028-v1'
REFERENCE_FREEZE_SHA='98d37a1f4eca10438f8789dcb7a2af40ecbab47bccd7842d69b787a5339ca9e5'
MAX_HOST_PACKET_BYTES=16*1024**2
MAX_OUTPUT_BYTES=16*1024**2
MAX_CALLS=33
POLICY='s-v1-small-first-repeat;large-repeat-or-small-large-small;retain-blocked'
def encoded(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def references():
    raw=(SOURCE/'pre-source-reference-freeze.json').read_bytes()
    if sha(raw)!=REFERENCE_FREEZE_SHA:raise ValueError('S pre-source freeze drift')
    freeze=json.loads(raw)
    for name,pin in freeze['files'].items():
        if sha((SOURCE/name).read_bytes())!=pin:raise ValueError('frozen source-free S owner drift')
    spec=importlib.util.spec_from_file_location('s_frozen_cases',SOURCE/'cases.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module,freeze

def packet(pid,rows,indices):return {'schema':'gamma.s-official-packet.v1','problem_id':pid,'calls':[{'args':rows[i]['args']} for i in indices]}

def successful_record(pid,args,want,language,oracle):
    classes={208:('Trie',{'insert'}),211:('WordDictionary',{'addWord'}),225:('MyStack',{'push'})}
    methods={199:'rightSideView',203:'removeElements',206:'reverseList',212:'findWords',214:'shortestPalindrome',222:'countNodes',224:'calculate'}
    is_class=pid in classes
    r={'native_route':'official-s-v1','problem_id':pid,'method':None if is_class else methods[pid],
       'entry_kind':('python-native-class' if language=='python' else 'javascript-native-class') if is_class else ('python-solution-method' if language=='python' else 'javascript-official-function'),
       'result':want,'result_type':None,'args_before':args,'args_after':args,'alias_edges':[],
       'node_identity':None,'node_integrity':None,'native_class':None,'native_receiver_count':None,'native_method_return_types':None,'native_method_snapshots':None,
       'entry_integrity':{'schema':'gamma.s-entry-integrity.v1','original_export_unchanged':True,'class_or_prototype_unchanged':True,'method_descriptor_unchanged':True,'fresh_receiver':True if language=='python' or is_class else None}}
    if is_class:
        name,void=classes[pid];types=['constructed']
        for method in args[0][1:]:
            types.append(('NoneType' if language=='python' else 'undefined') if method in void else ('bool' if language=='python' else 'boolean') if pid in (208,211) or method=='empty' else ('int' if language=='python' else 'number'))
        r.update(result_type='list' if language=='python' else 'object',native_class=name,native_receiver_count=1,native_method_return_types=types,native_method_snapshots=want)
    elif pid in (199,203,206,222):
        plan=oracle.effect_plan(pid,args);before=plan['pool_before'];after=[dict(row) for row in before];root=None;order=None
        if pid in (203,206):
            for i,row in enumerate(after):row['next']=plan['required_next'][i] if i in plan['required_next'] else {'external_identity':len(before)-1}
            root=want['head'];order=want['order'];r['alias_edges']=[] if root is None else [['result',f'args.0.pool.{root}']]
            r['result_type']=('NoneType' if root is None else 'ListNode') if language=='python' else 'object'
        else:r['result_type']=('list' if pid==199 else 'int') if language=='python' else ('object' if pid==199 else 'number')
        r['node_identity']={'before':before,'after':after,'argument_roots':plan['argument_roots'],'result_root':root,'result_order':order}
        r['node_integrity']={'schema':'gamma.s-native-integrity.v1','class_or_prototype_unchanged':True,'own_field_descriptors_unchanged':True,'original_node_classes_unchanged':True,'checked_node_count':len(before),'native_aliases_in_identity_table':True}
    else:r['result_type']=('list' if pid==212 else 'str' if pid==214 else 'int') if language=='python' else ('object' if pid==212 else 'string' if pid==214 else 'number')
    return r

def projection(pid,rows,language,oracle):
    costs=[]
    for row in rows:
        record=successful_record(pid,row['args'],row['expected'],language,oracle)
        # Max20digit packet index +256bytes cover newline/done, valid whole-result
        # input alias spelling and source-number serialization.203removedlinks
        # use worst sized permitted external marker; no actualsource inspected.
        costs.append(len(encoded({'i':10**19,**record}))+1+256)
    return costs

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
