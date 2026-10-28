"""Independent U257 host native/type/effect and unordered MULTISET checker."""
import hashlib
import importlib.util
from pathlib import Path
path=Path(__file__).resolve().parent.parent/'authored/continuation-u-20261028-v1/oracles.py'
if hashlib.sha256(path.read_bytes()).hexdigest()!='ff37bec489c3f397d4de5c93a2c381fdbee7ad1fbfdf786cce9629b337c0cd86':raise ValueError('independent reference drift')
spec=importlib.util.spec_from_file_location('u_reference',path);reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
exact=reference.exact
def check_observation(pid,args,row,language):
    try:
        reference.validate(pid,args)
        if language not in ('python','javascript') or type(row) is not dict:return False,'identity'
        keys={'native_route','problem_id','method','entry_kind','result','result_type','args_before','args_after','alias_edges','node_identity','node_integrity','entry_integrity'}
        if set(row) not in (keys,keys|{'i'}) or 'i' in row and (type(row['i']) is not int or not 0<=row['i']<33):return False,'shape'
        if type(row['problem_id']) is not int or row['problem_id']!=257 or row['native_route']!='official-u-v1' or row['method']!='binaryTreePaths' or row['entry_kind']!=('python-solution-method' if language=='python' else 'javascript-official-function'):return False,'official_entry'
        entry={'schema':'gamma.u-entry-integrity.v1','original_export_unchanged':True,'class_or_prototype_unchanged':True,'method_descriptor_unchanged':True,'fresh_receiver':True if language=='python' else None}
        node={'schema':'gamma.u-native-integrity.v1','class_or_prototype_unchanged':True,'own_field_descriptors_unchanged':True,'original_node_classes_unchanged':True,'checked_node_count':len(args[0]['values']),'native_aliases_in_identity_table':True}
        if not exact(row['entry_integrity'],entry) or not exact(row['node_integrity'],node) or not exact(row['alias_edges'],[]):return False,'native_integrity'
        if row['result_type']!=('list' if language=='python' else 'object'):return False,'result_type'
        return reference.check_observation(pid,args,row,language)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False,'invalid_observation'
