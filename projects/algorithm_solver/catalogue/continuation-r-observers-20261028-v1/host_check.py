"""R observation acceptance against frozen source-blind owners; never executes."""
import importlib.util
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'authored/continuation-r-20261028-v1'
SPEC=importlib.util.spec_from_file_location('r_frozen_semantic_owner',SOURCE/'oracles.py')
oracle=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(oracle)
FIELDS={'native_route','problem_id','result','result_type','args_before','args_after','alias_edges','node_identity','node_integrity','native_class','native_receiver_count','native_method_return_types','native_method_snapshots','method'}


def linked(rows,root):
    values=[];seen=set();i=root
    while i is not None:
        if type(i) is not int or not 0<=i<len(rows) or i in seen:raise ValueError('bad physical list traversal')
        seen.add(i);values.append(rows[i]['value']);i=rows[i]['next']
    return {'__list_node__':values}


def check(pid,args,record,language):
    try:
        oracle.validate(pid,args)
        if language not in ('python','javascript') or type(record) is not dict:return False,'observation_shape'
        if 'error' in record:return False,'candidate_error'
        if set(record)-{'i'}!=FIELDS or 'i' in record and (type(record['i']) is not int or record['i']<0):return False,'observation_fields'
        if type(record['problem_id']) is not int or record['problem_id']!=pid or record['native_route']!='official-r-v1':return False,'official_route'
        if not oracle.exact(record['args_before'],args):return False,'argument_before'
        if pid in oracle.CLASSES:
            if record['native_class']!=oracle.CLASSES[pid] or type(record['native_receiver_count']) is not int or record['native_receiver_count']!=1 or record['method'] is not None:return False,'class_receiver'
            if record['result_type']!=('list' if language=='python' else 'object') or not oracle.exact(record['result'],oracle.expected(pid,args)):return False,'class_values'
            if not oracle.exact(record['native_method_return_types'],oracle.class_return_types(pid,args,language)) or not oracle.exact(record['native_method_snapshots'],record['result']):return False,'class_method_types_or_snapshots'
        else:
            if record['method']!=oracle.METHODS[pid] or any(record[k] is not None for k in ('native_class','native_receiver_count','native_method_return_types','native_method_snapshots')):return False,'function_entry'
        if pid==147:
            state=record['node_identity']
            if not oracle.accepts_list_identity(args,state):return False,'147_physical_identity'
            if not oracle.exact(record['result'],oracle.expected(pid,args)) or not oracle.exact(record['args_after'],[linked(state['after'],0)]):return False,'147_list_values'
            if record['result_type']!=('ListNode' if language=='python' else 'object'):return False,'147_result_type'
        elif pid==160:
            state=record['node_identity']
            if not oracle.accepts_intersection_identity(args,state):return False,'160_shared_identity'
            root=oracle.expected(pid,args)
            value=None if root is None else linked(state['after'],root)
            if not oracle.exact(record['result'],value):return False,'160_result_value'
            if record['result_type']!=('NoneType' if root is None else 'ListNode') and language=='python' or language=='javascript' and record['result_type']!='object':return False,'160_result_type'
        elif pid==173:
            before=[{'id':i,**row} for i,row in enumerate(oracle.tree_nodes(args[1][0][0]))]
            state={'before':before,'after':before,'argument_roots':[0],'result_root':None}
            if not oracle.exact(record['node_identity'],state):return False,'173_local_tree_effect'
        elif pid==188:
            if not oracle.exact(record['result'],oracle.expected(pid,args)) or record['result_type']!=('int' if language=='python' else 'number'):return False,'188_value_or_type'
        if pid!=147 and not oracle.exact(record['args_after'],args):return False,'argument_after'
        if pid in (147,160,173):
            state=record['node_identity']
            if type(state) is not dict or set(state)!={'before','after','argument_roots','result_root'}:return False,'node_evidence_shape'
            integrity={'schema':'gamma.r-native-integrity.v1','class_or_prototype_unchanged':True,'own_field_descriptors_unchanged':True,'original_node_classes_unchanged':True,'acyclic_graphs':True,'checked_node_count':len(state['after']),'native_aliases_in_identity_table':True}
            if not oracle.exact(record['node_integrity'],integrity):return False,'physical_integrity'
            aliases=[] if state['result_root'] is None else [['result',f'args.{i}'] for i,root in enumerate(state['argument_roots']) if root==state['result_root']]
            if not oracle.exact(record['alias_edges'],aliases):return False,'native_root_aliases'
        elif record['node_identity'] is not None or record['node_integrity'] is not None or not oracle.exact(record['alias_edges'],[]):return False,'unexpected_native_evidence'
        return True,None
    except (ValueError,TypeError,KeyError,IndexError,RecursionError):return False,'invalid_observation'
