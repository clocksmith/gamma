"""Contract checks for mutation and alias preservation, not score expectations."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location("scale100_qualify",Path(__file__).with_name("qualify.py"));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_original_parity_rejects_changed_alias():
    case={"args":[[1,2]],"expected":[1,2]}
    rec={"args_before":[[1,2]],"args_after":[[1,2]],"result":[1,2],"alias_edges":[]}
    passed,obs=m.judge_record(54,case,"return",rec);assert passed
    changed={**rec,"alias_edges":[["result","args.0"]]}
    assert not m.judge_record(54,case,"return",changed,obs)[0]
def test_plus_one_preserves_return_identity():
    case={"args":[[9]],"expected":[1,0]}
    rec={"args_before":[[9]],"args_after":[[1,0]],"result":[1,0],"alias_edges":[["result","args.0"]]}
    assert m.judge_record(66,case,"return",rec)[0]
    assert not m.judge_record(66,case,"return",{**rec,"alias_edges":[]})[0]
def test_sort_mutation_is_not_blanket_allowed():
    case={"args":[[[3,4],[1,2]]],"expected":[[1,2],[3,4]]}
    rec={"args_before":case["args"],"args_after":[[[1,2],[3,4]]],"result":case["expected"],"alias_edges":[]}
    assert m.judge_record(56,case,"return",rec)[0]
    assert not m.judge_record(56,case,"return",{**rec,"args_after":[[]]})[0]
def test_wrong_output_and_boolean_confusion_rejected():
    case={"args":[[1,2]],"expected":3};rec={"args_before":case["args"],"args_after":case["args"],"result":2,"alias_edges":[]}
    assert not m.judge_record(54,case,"return",rec)[0]
    assert not m.exact([True],[1])
def test_subset_comparison_preserves_multiplicity_and_inner_order():
    case={"args":[[1,2]],"expected":[[],[1],[2],[1,2]]}
    rec={"args_before":case["args"],"args_after":case["args"],"result":[[1,2],[2],[1],[]],"alias_edges":[]}
    assert m.judge_record(78,case,"return:unordered_outer",rec)[0]
    assert not m.judge_record(78,case,"return:unordered_outer",{**rec,"result":[[],[1],[2],[2,1]]})[0]
    assert not m.judge_record(78,case,"return:unordered_outer",{**rec,"result":[[],[1],[2],[1,2],[1,2]]})[0]
