import copy

import pytest

from . import verify_node_identity as v
from . import verify_imported_semantics as semantic


def record(pid, args, after, result_root=0):
    before = v.decode_original(pid, args)
    return {'node_identity': {'before': before, 'after': after, 'argument_roots': [0], 'result_root': result_root},
            'args_before': [v.encode_graph(before, pid == 814)],
            'args_after': [v.encode_graph(after, pid == 814)],
            'alias_edges': [] if result_root is None else [['result', 'args.0']]}


def tree_fixture():
    args = [{'__tree_node__': [1, 0, 1, 0, 0, 0, 1]}]
    after = [{'value': 1, 'left': None, 'right': 2}, {'value': 0, 'left': None, 'right': None},
             {'value': 1, 'left': None, 'right': 6}, {'value': 0, 'left': None, 'right': None},
             {'value': 0, 'left': None, 'right': None}, {'value': 0, 'left': None, 'right': None},
             {'value': 1, 'left': None, 'right': None}]
    return args, record(814, args, after)


def test_pruning_retains_original_tree_ids_and_checks_detached_nodes():
    args, observation = tree_fixture()
    assert v.check(814, args, observation) is None
    damaged = copy.deepcopy(observation)
    # Node1 was pruned from the reachable root, but its own edits are observed.
    damaged['node_identity']['after'][1]['left'] = 3
    assert v.check(814, args, damaged) == 'node_identity_effects'
    damaged = copy.deepcopy(observation); damaged['node_identity']['after'][2]['value'] = 0
    assert v.check(814, args, damaged) == 'node_identity_effects'


def test_pruning_entire_tree_returns_null_but_keeps_mutated_argument_root():
    args = [{'__tree_node__': [0, 0, 0]}]
    after = [{'value': 0, 'left': None, 'right': None} for _ in range(3)]
    observation = record(814, args, after, None)
    assert observation['args_after'] == [{'__tree_node__': [0]}]
    assert v.check(814, args, observation) is None
    observation['node_identity']['result_root'] = 0
    assert v.check(814, args, observation) == 'node_identity_effects'


def test_even_groups_use_actual_final_size_and_preserve_values():
    args = [{'__list_node__': list(range(1, 9))}]
    # Groups: [0], [2,1], [3,4,5], [7,6] (partial final group has size2).
    following = [2, 3, 1, 4, 5, 7, None, 6]
    observation = record(2074, args, [{'value': i+1, 'next': following[i]} for i in range(8)])
    assert v.check(2074, args, observation) is None
    damaged = copy.deepcopy(observation); damaged['node_identity']['after'][6]['next'] = 7
    assert v.check(2074, args, damaged) == 'node_identity_effects'


def gcd_fixture():
    args = [{'__list_node__': [18, 6, 10]}]
    after = [{'value': 18, 'next': 3}, {'value': 6, 'next': 4}, {'value': 10, 'next': None},
             {'value': 6, 'next': 1}, {'value': 2, 'next': 2}]
    return args, record(2807, args, after)


def test_gcd_nodes_are_fresh_and_original_head_survives():
    args, observation = gcd_fixture()
    assert v.check(2807, args, observation) is None
    damaged = copy.deepcopy(observation); damaged['node_identity']['after'][3]['value'] = 7
    assert v.check(2807, args, damaged) == 'node_identity_effects'
    damaged = copy.deepcopy(observation); damaged['node_identity']['result_root'] = 3
    assert v.check(2807, args, damaged) == 'node_identity_effects'
    damaged = copy.deepcopy(observation); damaged['node_identity']['after'][3]['next'] = 0
    assert v.check(2807, args, damaged) == 'node_identity_effects'


@pytest.mark.parametrize('mutation', ['missing', 'counterfeit-before', 'bool-pointer', 'bool-root', 'new-original-copy', 'wrong-alias', 'wrong-serialization'])
def test_rejects_forged_or_inconsistent_identity_evidence(mutation):
    args, observation = gcd_fixture()
    if mutation == 'missing': del observation['node_identity']
    elif mutation == 'counterfeit-before': observation['node_identity']['before'][0]['value'] = 0
    elif mutation == 'bool-pointer': observation['node_identity']['after'][3]['next'] = True
    elif mutation == 'bool-root': observation['node_identity']['result_root'] = False
    elif mutation == 'new-original-copy': observation['node_identity']['after'].append({'value': 18, 'next': 3})
    elif mutation == 'wrong-alias': observation['alias_edges'] = []
    elif mutation == 'wrong-serialization': observation['args_after'] = args
    assert v.check(2807, args, observation) is not None


def test_semantic_dispatch_requires_identity_after_matching_values():
    args, observation = gcd_fixture()
    output = {'__list_node__': [18, 6, 6, 2, 10]}
    observation.update(result=output, result_type='ListNode')
    case = {'args': args, 'expected': output}
    assert semantic.compare(2807, case, observation, 'python') is None
    del observation['node_identity']
    assert semantic.compare(2807, case, observation, 'python') == 'node_identity_effects'
