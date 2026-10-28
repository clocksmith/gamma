"""S host bridge: full official ABI/type/integrity plus source-blind semantics/effects.
This file and independent expectations NEVER enter a candidate child.
"""
import importlib.util
from pathlib import Path
_SPEC=importlib.util.spec_from_file_location('s_independent_owner_reference',Path(__file__).resolve().parent.parent/'authored/continuation-s-20261028-v1/oracles.py')
reference=importlib.util.module_from_spec(_SPEC);_SPEC.loader.exec_module(reference)
IDS=(199,203,206,208,211,212,214,222,224,225)
METHODS={199:'rightSideView',203:'removeElements',206:'reverseList',212:'findWords',214:'shortestPalindrome',222:'countNodes',224:'calculate'}
CLASSES={208:('Trie',{'insert'}),211:('WordDictionary',{'addWord'}),225:('MyStack',{'push'})}
NATIVE=(199,203,206,222)
exact=reference.exact

def expected(pid,args):return reference.expected(pid,args)

def packet(pid,cases):
    if type(pid) is not int or pid not in IDS or type(cases) is not list or not 1<=len(cases)<=33:raise ValueError('fixed S packet identity')
    calls=[]
    for row in cases:
        args=row['args'];reference.validate(pid,args);calls.append({'args':args})
    return {'schema':'gamma.s-official-packet.v1','problem_id':pid,'calls':calls}

def aliases_valid_212(args,result,edges):
    if exact(edges,[]):return True
    if type(edges) is not list or len(edges)!=1 or type(edges[0]) is not list or len(edges[0])!=2 or edges[0][0]!='result' or type(edges[0][1]) is not str:return False
    path=edges[0][1].split('.')
    if not path or path[0]!='args':return False
    current=args
    for part in path[1:]:
        if type(current) is not list or not part.isascii() or not part.isdecimal():return False
        index=int(part)
        if not 0<=index<len(current):return False
        current=current[index]
    return type(current) is list and exact(current,result)

def check_observation(pid,args,record,language):
    try:
        if type(pid) is not int or pid not in IDS or language not in ('python','javascript'):return False,'identity'
        reference.validate(pid,args)
        if type(record) is not dict or 'error' in record:return False,'observation_error'
        keys={'native_route','problem_id','method','entry_kind','result','result_type','args_before','args_after','alias_edges','node_identity','node_integrity','entry_integrity','native_class','native_receiver_count','native_method_return_types','native_method_snapshots'}
        if set(record) not in (keys,keys|{'i'}) or ('i' in record and (type(record['i']) is not int or not 0<=record['i']<33)):return False,'observation_keys'
        is_class=pid in CLASSES
        kind=('python-native-class' if language=='python' else 'javascript-native-class') if is_class else ('python-solution-method' if language=='python' else 'javascript-official-function')
        if record.get('native_route')!='official-s-v1' or type(record.get('problem_id')) is not int or record['problem_id']!=pid or record.get('entry_kind')!=kind or record.get('method')!=(None if is_class else METHODS[pid]):return False,'official_entry'
        integrity={'schema':'gamma.s-entry-integrity.v1','original_export_unchanged':True,'class_or_prototype_unchanged':True,'method_descriptor_unchanged':True,'fresh_receiver':True if language=='python' or is_class else None}
        if not exact(record.get('entry_integrity'),integrity):return False,'entry_integrity'
        if not reference.accepts_result(pid,args,record.get('result')):return False,'wrong_answer'
        effects,reason=reference.check_effects(pid,args,record)
        if not effects:return False,reason
        if is_class:
            name,void=CLASSES[pid];ops=args[0];wanted=expected(pid,args)
            if record.get('native_class')!=name or not exact(record.get('native_receiver_count'),1) or not exact(record.get('native_method_snapshots'),wanted):return False,'native_receiver_or_snapshots'
            types=['constructed']
            for method in ops[1:]:
                if method in void:types.append('NoneType' if language=='python' else 'undefined')
                elif pid in (208,211) or method=='empty':types.append('bool' if language=='python' else 'boolean')
                else:types.append('int' if language=='python' else 'number')
            if not exact(record.get('native_method_return_types'),types) or record.get('result_type')!=('list' if language=='python' else 'object'):return False,'native_return_types'
            if record.get('node_identity') is not None or record.get('node_integrity') is not None or not exact(record.get('alias_edges'),[]):return False,'class_node_or_alias_evidence'
            return True,None
        if any(record.get(key) is not None for key in ('native_class','native_receiver_count','native_method_return_types','native_method_snapshots')):return False,'unexpected_trace_fields'
        result=record['result']
        if pid in NATIVE:
            n=len(args[0]['values']);identity=record.get('node_identity')
            if type(identity) is not dict or set(identity)!={'before','after','argument_roots','result_root','result_order'}:return False,'node_record_shape'
            node_integrity={'schema':'gamma.s-native-integrity.v1','class_or_prototype_unchanged':True,'own_field_descriptors_unchanged':True,'original_node_classes_unchanged':True,'checked_node_count':n,'native_aliases_in_identity_table':True}
            if not exact(record.get('node_integrity'),node_integrity):return False,'node_integrity'
            if pid in (203,206):
                retained=set(result['order']);after=identity['after']
                for i,row in enumerate(after):
                    value=row['next']
                    if value is None or type(value) is int and 0<=value<n:continue
                    if pid!=203 or i in retained or type(value) is not dict or set(value)!={'external_identity'} or type(value['external_identity']) is not int or not 0<=value['external_identity']<n:return False,'native_pointer_identity'
                root=result['head'];edges=[] if root is None else [['result',f'args.0.pool.{root}']]
                if not exact(record.get('alias_edges'),edges):return False,'result_alias_identity'
                wanted_type=('NoneType' if root is None else 'ListNode') if language=='python' else 'object'
            else:
                if not exact(record.get('alias_edges'),[]):return False,'tree_result_alias'
                wanted_type=('list' if pid==199 else 'int') if language=='python' else ('object' if pid==199 else 'number')
            if record.get('result_type')!=wanted_type:return False,'native_result_type'
        else:
            if record.get('node_identity') is not None or record.get('node_integrity') is not None:return False,'unexpected_node_evidence'
            wanted_type=('list' if pid==212 else 'str' if pid==214 else 'int') if language=='python' else ('object' if pid==212 else 'string' if pid==214 else 'number')
            if record.get('result_type')!=wanted_type:return False,'result_type'
            if pid==212:
                if not aliases_valid_212(args,result,record.get('alias_edges')):return False,'board_result_alias'
            elif not exact(record.get('alias_edges'),[]):return False,'scalar_alias'
        return True,None
    except (KeyError,ValueError,TypeError,IndexError,AttributeError):return False,'invalid_observation_or_contract'
