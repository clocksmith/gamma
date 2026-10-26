from copy import deepcopy
from .node_identity_contracts import check
from .imported_result_contracts import canonical, exact


def test_equal_values_cannot_hide_wrong_node_order():
    args=[{'__list_node__':[1]*5}]
    before=[{'value':1,'next':i+1 if i<4 else None}for i in range(5)]
    after=[{'value':1,'next':v}for v in (2,4,1,None,3)]
    record={'node_identity':{'before':before,'after':after,'argument_roots':[0],'result_root':0},'args_before':args,'args_after':args,'alias_edges':[['result','args.0']]}
    assert check(2074,args,record,exact,canonical)is None
    wrong=deepcopy(record);wrong['node_identity']['after']=before
    assert check(2074,args,wrong,exact,canonical)=='node_identity_effects'


def test_insertions_preserve_originals_even_when_all_values_equal():
    args=[{'__list_node__':[6,6]}]
    before=[{'value':6,'next':1},{'value':6,'next':None}]
    after=[{'value':6,'next':2},{'value':6,'next':None},{'value':6,'next':1}]
    record={'node_identity':{'before':before,'after':after,'argument_roots':[0],'result_root':0},'args_before':args,'args_after':[{'__list_node__':[6,6,6]}],'alias_edges':[['result','args.0']]}
    assert check(2807,args,record,exact,canonical)is None
    wrong=deepcopy(record);wrong['node_identity']['result_root']=2
    assert check(2807,args,wrong,exact,canonical)=='node_identity_effects'


def test_pruning_retains_root_and_records_detached_nodes():
    args=[{'__tree_node__':[1,0,1]}]
    before=[{'value':1,'left':1,'right':2},{'value':0,'left':None,'right':None},{'value':1,'left':None,'right':None}]
    after=deepcopy(before);after[0]['left']=None
    record={'node_identity':{'before':before,'after':after,'argument_roots':[0],'result_root':0},'args_before':args,'args_after':[{'__tree_node__':[1,None,1]}],'alias_edges':[['result','args.0']]}
    assert check(814,args,record,exact,canonical)is None
    wrong=deepcopy(record);wrong['node_identity']['after'][1]['value']=1
    assert check(814,args,wrong,exact,canonical)=='node_identity_effects'
