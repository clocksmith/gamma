import copy
import itertools

import pytest

from . import verify_imported_semantics as v


def test_constructive_empty_results_do_not_trust_bad_expected():
    assert not v.result_valid(936, ['ab', 'abab'], [], [])
    assert v.result_valid(936, ['ab', 'aa'], [], [0])
    assert not v.result_valid(1203, [2, 1, [0, 0], [[], [0]]], [], [])
    assert v.result_valid(1203, [2, 1, [0, 0], [[1], [0]]], [], [0, 1])
    assert not v.result_valid(2392, [2, [[1, 2]], []], [], [])
    assert v.result_valid(2392, [2, [[1, 2], [2, 1]], []], [], [[1, 0], [0, 2]])


def test_group_contiguity_and_dependency_are_both_required():
    args = [4, 2, [0, 0, 1, 1], [[], [2], [0], []]]
    assert not v.groups_possible(args[0], args[2], args[3])
    assert not v.result_valid(1203, args, [0, 2, 1, 3], [])
    assert v.result_valid(1203, [4, 2, [0, 0, 1, 1], [[], [], [], []]], [2, 3, 0, 1], [])


def test_reverse_stamping_matches_small_exhaustive_forward_reachability():
    for stamp_len in (1, 2):
        for stamp_tuple in itertools.product('ab', repeat=stamp_len):
            stamp = ''.join(stamp_tuple)
            for size in range(stamp_len, 5):
                states, pending = {'?'*size}, ['?'*size]
                while pending:
                    state = pending.pop()
                    for start in range(size-stamp_len+1):
                        successor = state[:start]+stamp+state[start+stamp_len:]
                        if successor not in states:
                            states.add(successor); pending.append(successor)
                for target_tuple in itertools.product('ab', repeat=size):
                    target = ''.join(target_tuple)
                    assert v.stamp_possible(stamp, target) == (target in states)


def test_balanced_bst_checks_values_structure_order_and_height():
    old = {'__tree_node__': [1, None, 2, None, 3]}
    assert v.balanced_bst({'__tree_node__': [2, 1, 3]}, old)
    assert not v.balanced_bst(old, old)
    assert not v.balanced_bst({'__tree_node__': [2, 3, 1]}, old)
    with pytest.raises(ValueError): v.balanced_bst({'__tree_node__': [1, None, None, 2]}, old)


def test_path_optimum_is_derived_not_copied_from_expected():
    args = [3, [[0, 1], [1, 2]], ['a', 'b', 'a'], ['a', 'b', 'a']]
    assert v.result_valid(1548, args, [2, 1, 0], [1, 0, 1])
    assert not v.result_valid(1548, args, [1, 0, 1], [1, 0, 1])
    assert not v.result_valid(1548, args, [0, 2, 0], [])


def test_subset_sum_multiplicity_and_integer_types():
    assert v.result_valid(1982, [2, [0, 0, 1, 1]], [0, 1], [])
    assert not v.result_valid(1982, [2, [0, 0, 1, 1]], [True, 0], [])
    assert not v.result_valid(1982, [2, [0, 0, 1, 1]], [1, 1], [])


def test_list_alias_is_required_and_no_unrelated_alias_allowed():
    case = {'args': [{'__list_node__': [1, 2, 3, 4]}], 'expected': {'__list_node__': [3, 4]}}
    record = {'result': case['expected'], 'result_type': 'ListNode',
              'args_before': case['args'], 'args_after': case['args'], 'alias_edges': [['result', 'args.0.next.next']]}
    assert v.compare(876, case, record, 'python') is None
    broken = copy.deepcopy(record); broken['alias_edges'] = []
    assert v.compare(876, case, broken, 'python') == 'return_aliases'
    broken = copy.deepcopy(record); broken['args_after'][0]['__list_node__'][0] = 9
    assert v.compare(876, case, broken, 'python') == 'input_effects'


def test_large_integer_tags_and_null_tree_transport():
    case = {'args': [2], 'expected': 2**60}
    record = {'result': {'__gamma_bigint_v1__': str(2**60)}, 'result_type': 'bigint',
              'args_before': [2], 'args_after': [2], 'alias_edges': []}
    assert v.compare(1, case, record, 'javascript') is None
    record['result'] = {'__gamma_bigint_v1__': '0'+str(2**60)}
    assert v.compare(1, case, record, 'javascript') == 'result_value'
    assert v.normalized({'__tree_node__': []}) is None
    assert v.normalized({'__tree_node__': [1, None, None]}) == {'__tree_node__': [1]}


def test_set_and_peak_checks_reject_duplicate_or_boolean_answers():
    assert v.result_valid(1606, [], [2, 1], [1, 2])
    assert not v.result_valid(1606, [], [1, 1, 2], [1, 2])
    assert not v.result_valid(1606, [], [True, 2], [1, 2])
    assert v.result_valid(1901, [[[1, 4], [3, 2]]], [0, 1], [1, 0])
    assert not v.result_valid(1901, [[[1, 4], [3, 2]]], [1, 1], [1, 1])


def test_absolute_numeric_bounds_and_exact_half_integer_policy():
    for pid in (813, 1377, 1701):
        assert not v.result_valid(pid, [], 100000001.0, 100000000.0)
        assert v.result_valid(pid, [], 3.0 + 1e-7, 3.0)
        assert not v.result_valid(pid, [], True, 1)
    assert v.result_valid(3194, [], 3.5, 3.5)
    assert not v.result_valid(3194, [], 3.500000001, 3.5)


def test_doubled_array_constructive_and_impossibility():
    assert v.result_valid(2007, [[0, 0, 1, 2]], [1, 0], [])
    assert not v.result_valid(2007, [[0, 0, 1, 2]], [], [])
    assert v.result_valid(2007, [[0, 1, 2]], [], [1])
    assert v.result_valid(2007, [[1, 3]], [], [1])
    assert not v.result_valid(2007, [[1, 2]], [True], [1])
