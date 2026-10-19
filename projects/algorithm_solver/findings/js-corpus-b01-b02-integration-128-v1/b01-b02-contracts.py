"""Opt-in corrections for reviewed wave identities; frozen inputs stay immutable."""
from dataclasses import replace
from copy import deepcopy
from algsolve import validate

def prepare(problem, raw_tests):
    identity=(problem.uid,problem.slug,problem.entry.get('method'))
    if identity not in {('lcd:23','merge-k-sorted-lists','mergeKLists'),('lcd:30','substring-with-concatenation-of-all-words','findSubstring')}:
        raise ValueError('Unreviewed identity')
    if not raw_tests or any(t.get('kwargs') or t.get('compare','return')!='return' for t in raw_tests):
        raise ValueError('Unsupported contract')
    tests=validate.functional_tests(raw_tests)
    if problem.uid=='lcd:30':
        return [replace(t,compare='return:unordered_outer') for t in tests]
    if problem.params != [['lists','List[Optional[ListNode]]']]:
        raise ValueError('Unexpected nested-list signature')
    def node(value):
        if value is None: return None
        if isinstance(value,dict) and set(value)=={'__list_node__'}:
            if not isinstance(value['__list_node__'],list):raise ValueError('Invalid node tag')
            return deepcopy(value)
        if isinstance(value,list):return {'__list_node__':deepcopy(value)}
        raise ValueError('Unsupported list representation')
    result=[]
    for t in tests:
        if len(t.args)!=1 or not isinstance(t.args[0],list):raise ValueError('Invalid list argument')
        result.append(replace(t,args=[[node(v) for v in t.args[0]]]))
    return result
