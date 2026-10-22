"""Oracle rule for admission qualification: scale150-v1 qualify.judge with no prior variant."""
from algsolve.judge.judge import FunctionalTest, _matches


def normalize(x):
    if isinstance(x, list): return [normalize(v) for v in x]
    if isinstance(x, dict):
        if x == {'__list_node__': []} or x == {'__tree_node__': []}: return None
        if set(x) == {'__gamma_bigint_v1__'}: return int(x['__gamma_bigint_v1__'])
        return {k: normalize(v) for k, v in x.items()}
    return x


def judge_case(case, rec):
    observed = {k: rec.get(k) for k in ['result', 'result_type', 'args_before', 'args_after', 'alias_edges', 'error']}
    expected = normalize(case['expected']); actual = normalize(rec.get('result'))
    valid = not rec.get('error') and _matches(FunctionalTest(args=case['args'], expected=expected, compare=case.get('compare', 'return')), {'result': actual})
    if isinstance(expected, int) and not isinstance(expected, bool) and abs(expected) > 2 ** 53 - 1:
        valid = valid and rec.get('result_type') == 'bigint'
    return bool(valid), observed
