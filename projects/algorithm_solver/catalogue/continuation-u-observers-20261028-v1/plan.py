"""Prospective T argument-only packet/output envelopes, no candidate/runtime work.
Uses the current R-lane16MiB host envelopes as planning ceilings only; execution
owner must confirm unchanged actual caps. Smaller-cap exclusions remain explicit.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'authored/continuation-u-20261028-v1'
REFERENCE_FREEZE_SHA='dd9d61d32fd76592edfa38e36c812a80ec5b173b85a5450f24b571470ae631f3'
MAX_HOST_PACKET_BYTES=16*1024**2
MAX_OUTPUT_BYTES=16*1024**2
MAX_CALLS=33
POLICY='u-v1-small-first-repeat;large-repeat-or-small-large-small;retain-blocked'
def encoded(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def references():
    raw=(SOURCE/'pre-source-reference-freeze.json').read_bytes()
    if sha(raw)!=REFERENCE_FREEZE_SHA:raise ValueError('T pre-source freeze drift')
    freeze=json.loads(raw)
    for name,pin in freeze['files'].items():
        if sha((SOURCE/name).read_bytes())!=pin:raise ValueError('frozen source-free T owner drift')
    spec=importlib.util.spec_from_file_location('u_frozen_cases',SOURCE/'cases.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module,freeze

def packet(pid,rows,indices):return {'schema':'gamma.u-official-packet.v1','problem_id':pid,'calls':[{'args':rows[i]['args']} for i in indices]}

def successful_record(pid,args,want,language,oracle):
    oracle.validate(pid,args);plan=oracle.effect_plan(pid,args)
    return {'native_route':'official-u-v1','problem_id':pid,'method':'binaryTreePaths','entry_kind':'python-solution-method' if language=='python' else 'javascript-official-function','result':want,'result_type':'list' if language=='python' else 'object','args_before':args,'args_after':args,'alias_edges':[],
      'node_identity':{k:plan[k] for k in ('before','after','argument_roots','fixture_roots','result_root','result_order')},
      'node_integrity':{'schema':'gamma.u-native-integrity.v1','class_or_prototype_unchanged':True,'own_field_descriptors_unchanged':True,'original_node_classes_unchanged':True,'checked_node_count':len(args[0]['values']),'native_aliases_in_identity_table':True},
      'entry_integrity':{'schema':'gamma.u-entry-integrity.v1','original_export_unchanged':True,'class_or_prototype_unchanged':True,'method_descriptor_unchanged':True,'fresh_receiver':True if language=='python' else None}}

def projection(pid,rows,language,oracle):
    costs=[]
    for row in rows:
        record=successful_record(pid,row['args'],row['expected'],language,oracle)
        # Max20digit packet index +256bytes cover newline/done, valid whole-result
        # pointer-alias spelling and source-number serialization. All native
        # effects are fixed by selected source contracts; no source body read.
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
