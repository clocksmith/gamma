"""T host official-route/type/identity bridge. Never copied into child."""
import importlib.util
import hashlib
from pathlib import Path
_REFERENCE=Path(__file__).resolve().parent.parent/'authored/continuation-t-20261028-v1/oracles.py'
if hashlib.sha256(_REFERENCE.read_bytes()).hexdigest()!='2ec3605800a982a50c30d5e323cf14be3ff8c3874da9388422637c121c367617':raise ValueError('pinned independent T reference drift')
_SPEC=importlib.util.spec_from_file_location('t_independent_owner_reference',_REFERENCE)
reference=importlib.util.module_from_spec(_SPEC);_SPEC.loader.exec_module(reference)
IDS=(226,230,232,233,234,235,236,237)
BLOCKED_IDS=(243,245)
METHODS={226:'invertTree',230:'kthSmallest',233:'countDigitOne',234:'isPalindrome',235:'lowestCommonAncestor',236:'lowestCommonAncestor',237:'deleteNode'}
NATIVE=(226,230,234,235,236,237)
exact=reference.exact

def expected(pid,args):return reference.expected(pid,args)
def packet(pid,cases):
    if type(pid) is not int or pid not in IDS or type(cases) is not list or not 1<=len(cases)<=33:raise ValueError('fixed T active packet identity')
    calls=[]
    for row in cases:
        reference.validate(pid,row['args']);calls.append({'args':row['args']})
    return {'schema':'gamma.t-official-packet.v1','problem_id':pid,'calls':calls}

def pointer_aliases(result_root,argument_roots):
    if result_root is None:return []
    return sorted([['result',f'args.0.pool.{result_root}']]+[['result',f'args.{i}'] for i,index in enumerate(argument_roots) if index==result_root])

def check_observation(pid,args,record,language):
    try:
        if type(pid) is not int or pid not in IDS or language not in ('python','javascript'):return False,'identity_or_unavailable'
        reference.validate(pid,args)
        if type(record) is not dict or 'error' in record:return False,'observation_error'
        keys={'native_route','problem_id','method','entry_kind','result','result_type','args_before','args_after','alias_edges','node_identity','node_integrity','entry_integrity','native_class','native_receiver_count','native_method_return_types','native_method_snapshots'}
        if set(record) not in (keys,keys|{'i'}) or ('i' in record and (type(record['i']) is not int or not 0<=record['i']<33)):return False,'observation_keys'
        is_class=pid==232;kind=('python-native-class' if language=='python' else 'javascript-native-class') if is_class else ('python-solution-method' if language=='python' else 'javascript-official-function')
        if record.get('native_route')!='official-t-v1' or type(record.get('problem_id')) is not int or record['problem_id']!=pid or record.get('entry_kind')!=kind or record.get('method')!=(None if is_class else METHODS[pid]):return False,'official_entry'
        integrity={'schema':'gamma.t-entry-integrity.v1','original_export_unchanged':True,'class_or_prototype_unchanged':True,'method_descriptor_unchanged':True,'fresh_receiver':True if language=='python' or is_class else None}
        if not exact(record.get('entry_integrity'),integrity):return False,'entry_integrity'
        if not reference.accepts_result(pid,args,record.get('result')):return False,'wrong_answer'
        effects,reason=reference.check_effects(pid,args,record)
        if not effects:return False,reason
        if is_class:
            wanted=expected(pid,args);types=['constructed']
            for method in args[0][1:]:types.append(('NoneType' if language=='python' else 'undefined') if method=='push' else ('bool' if language=='python' else 'boolean') if method=='empty' else ('int' if language=='python' else 'number'))
            if record.get('native_class')!='MyQueue' or not exact(record.get('native_receiver_count'),1) or not exact(record.get('native_method_snapshots'),wanted) or not exact(record.get('native_method_return_types'),types):return False,'native_trace_evidence'
            if record.get('result_type')!=('list' if language=='python' else 'object') or record.get('node_identity') is not None or record.get('node_integrity') is not None or not exact(record.get('alias_edges'),[]):return False,'native_trace_type_or_alias'
            return True,None
        if any(record.get(key) is not None for key in ('native_class','native_receiver_count','native_method_return_types','native_method_snapshots')):return False,'unexpected_trace_fields'
        if pid in NATIVE:
            n=len(args[0]['values']);identity=record.get('node_identity')
            if type(identity) is not dict or set(identity)!={'before','after','argument_roots','fixture_roots','result_root','result_order'}:return False,'node_record_shape'
            node_integrity={'schema':'gamma.t-native-integrity.v1','class_or_prototype_unchanged':True,'own_field_descriptors_unchanged':True,'original_node_classes_unchanged':True,'checked_node_count':n,'native_aliases_in_identity_table':True}
            if not exact(record.get('node_integrity'),node_integrity):return False,'node_integrity'
            fields=('left','right') if pid in (226,230,235,236) else ('next',)
            after=identity['after']
            if type(after) is not list or len(after)!=n:return False,'native_pool_size'
            for row in after:
                if type(row) is not dict or set(row)!={'value',*fields} or type(row['value']) is not int:return False,'native_field_shape'
                for field in fields:
                    index=row[field]
                    if index is not None and (type(index) is not int or not 0<=index<n):return False,'native_pointer_identity'
            if pid in (226,235,236):
                root=identity['result_root'];wanted_type=('NoneType' if root is None else 'TreeNode') if language=='python' else 'object'
                edges=pointer_aliases(root,identity['argument_roots'])
            else:
                edges=[]
                wanted_type=('NoneType' if pid==237 else 'bool' if pid==234 else 'int') if language=='python' else ('undefined' if pid==237 else 'boolean' if pid==234 else 'number')
            if not exact(record.get('alias_edges'),edges):return False,'exact_pointer_aliases'
            if record.get('result_type')!=wanted_type:return False,'native_result_type'
        else:
            if record.get('node_identity') is not None or record.get('node_integrity') is not None or not exact(record.get('alias_edges'),[]):return False,'scalar_node_or_alias_evidence'
            if record.get('result_type')!=('int' if language=='python' else 'number'):return False,'scalar_type'
        return True,None
    except (KeyError,ValueError,TypeError,IndexError,AttributeError):return False,'invalid_observation_or_contract'
