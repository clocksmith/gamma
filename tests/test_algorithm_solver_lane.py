"""Focused tests for algorithm_solver parsing, matching and reporting logic."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

_LANE = Path(__file__).resolve().parents[1] / "projects" / "algorithm_solver"
if str(_LANE) not in sys.path:
    sys.path.insert(0, str(_LANE))

from algsolve import importers, lookup, report, values  # noqa: E402


def test_restricted_evaluator_never_calls_arbitrary_functions():
    with pytest.raises(values.Unsupported):
        values.parse_value("__import__('os').system('true')")
    with pytest.raises(values.Unsupported):
        values.parse_value("[x for x in range(3)]")
    with pytest.raises(values.Unsupported):
        values.parse_value("'a' * 10**9")
    assert values.parse_value("[1, -2] * 2 + [3]") == [1, -2, 1, -2, 3]
    assert values.parse_value("list_node([1, 2])") == {"__list_node__": [1, 2]}


def test_dataset_asserts_become_positional_tests():
    source = (
        "def check(candidate):\n"
        "    assert candidate(nums = [2, 7], target = 9) == [0, 1]\n"
        "    assert is_same_list(candidate(head = list_node([1, 2])), list_node([2, 1]))\n"
        "    assert candidate(nums = [i for i in range(3)], target = 1) == [0]\n"
    )
    params = [("nums", "List[int]"), ("target", "int")]
    tests, dropped = importers.lcd_hidden_tests(source, params)
    assert tests == [{"args": [[2, 7], 9], "expected": [0, 1], "compare": "return"}]
    assert dropped == 2  # unknown parameter `head`, and a comprehension


def test_canonical_forms_match_harness_serialization():
    assert values.canonicalize({"__list_node__": []}) is None
    assert values.canonicalize({"__tree_node__": [1, None, 2, None, None]}) == {"__tree_node__": [1, None, 2]}
    assert values.wrap_for_annotation([[1, 2], [3]], "List[Optional[ListNode]]") == [
        {"__list_node__": [1, 2]}, {"__list_node__": [3]}
    ]


def test_starter_code_with_docstring_and_design_stubs_parse():
    starter = 'class Solution:\n    def rotate(self, nums: List[int], k: int) -> None:\n        """\n        Do not return.\n        """\n'
    assert values.signature(starter, "rotate") == [("nums", "List[int]"), ("k", "int")]
    design = "class Router:\n    def __init__(self, n: int):\n\n    def add(self, x: int) -> bool:\n"
    assert values.signature(design, "add") == [("x", "int")]


def test_sibling_fingerprints_differ_on_constraints():
    one = "You are a robber planning to rob houses along a street. Constraints: 1 <= nums.length <= 100\nclass Solution:\n    def rob(self, nums: List[int]) -> int:\n"
    two = "All houses at this place are arranged in a circle. Constraints: 1 <= nums.length <= 100\nclass Solution:\n    def rob(self, nums: List[int]) -> int:\n"
    a, b = lookup.fingerprint(one), lookup.fingerprint(two)
    assert a.method == b.method == "rob"
    assert "circle" in b.phrases and "circle" not in a.phrases
    bonus_same = lookup.feature_bonus(b, b)
    bonus_cross = lookup.feature_bonus(b, a)
    assert bonus_same["phrases"] > bonus_cross["phrases"]


def test_decision_requires_score_and_margin():
    candidates = [{"key": "a", "score": 1.30}, {"key": "b", "score": 1.28}]
    th = {"min_score": 1.0, "min_margin": 0.05}
    assert lookup.decide(candidates, th).decision == "abstain"
    candidates[1]["score"] = 1.10
    result = lookup.decide(candidates, th)
    assert result.decision == "match" and result.key == "a"


def test_threshold_fit_prefers_zero_wrong_matches():
    dev = [
        ([{"key": "a", "score": 1.4}, {"key": "x", "score": 1.0}], "a"),
        ([{"key": "y", "score": 1.2}, {"key": "z", "score": 1.15}], None),
        ([{"key": "b", "score": 1.35}, {"key": "c", "score": 1.30}], "c"),
    ]
    th = lookup.fit_thresholds(dev)
    assert th["dev_wrong"] == 0 and th["dev_correct"] == 1


def test_adapt_renames_method_only_when_needed():
    entry = type("E", (), {"entry": {"class": "Solution", "method": "rob"}})()
    code = "class Solution:\n    def rob(self, nums):\n        return 0\n"
    assert lookup.adapt_solution(code, entry, "rob") == code
    assert "def robCircle" in lookup.adapt_solution(code, entry, "robCircle")


def test_recognition_outcomes_and_grouping():
    records = [
        {"qid": "1", "group": "known:a", "kind": "exact", "target": "lc:a", "decision": "match", "matched": "lc:a", "lookup_seconds": 0.1},
        {"qid": "2", "group": "known:a", "kind": "paraphrase", "target": "lc:a", "decision": "abstain", "matched": None, "lookup_seconds": 0.1},
        {"qid": "3", "group": "absent:b", "kind": "absent_exact", "target": None, "decision": "match", "matched": "lc:c", "lookup_seconds": 0.1},
    ]
    summary = report.recognition_summary(records, {"recognition": records})
    assert summary["groups"] == 2
    assert summary["group_correct_decision_rate"]["value"] == 0.25  # (0.5 + 0.0) / 2 groups
    assert summary["group_wrong_match_rate"]["value"] == 0.5
    assert summary["outcomes_by_query_kind"]["absent_exact"] == {"wrong_match": 1}
