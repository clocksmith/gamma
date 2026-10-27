"""Queue 08 subset 03 bounded specification references, not candidate evidence.

Earlier unsolicited development snippets for 3085 remain disclosed; this is not
an untouched holdout or globally fresh source-blind experiment. No candidates run.
"""
from __future__ import annotations
import ast
from collections import Counter
from itertools import islice, product
import json
import random
import re
import string
from . import imported_qualification as q
from .imported_clean_domains import integer, ints, text

IDS = (3081, 3085, 3096, 3101, 3106)
PARAMETERS = {3081: ('s',), 3085: ('word', 'k'), 3096: ('possible',), 3101: ('nums',), 3106: ('s', 'k')}
STATEMENT_SHA256 = {3081: '09fa673a79c3745779d3961aa1cd3d3f146fff83c1d9a0a59e0bf8da6e6b1d71', 3085: 'b2d484f27057dee9e29ac929ffe9790b3177bb1cec7b1fb990ae6870fe46af76', 3096: '31fa9390a9cf004310a6c12ccfad93b0f78bb5f626c58c0f50147a9ee437c88f', 3101: '8345c623a1fc1511d0a583892bedc5feba8b4c6b74fb8a51b210b8d8a7df2737', 3106: '4d36bfa542f592a3721c8b7900892c707e868aaf5beb80ed1b929aeccdd8594c'}
TITLES = {3081: 'Replace Question Marks in String to Minimize Its Value', 3085: 'Minimum Deletions to Make String K-Special', 3096: 'Minimum Levels to Gain More Points', 3101: 'Count Alternating Subarrays', 3106: 'Lexicographically Smallest String After Operations With Constraint'}
EXAMPLE_COUNT = {3081: 2, 3085: 3, 3096: 3, 3101: 2, 3106: 3}
CASE_COUNT = {3081: 373, 3085: 1517, 3096: 8240, 3101: 8243, 3106: 5481}
CASES_SHA256 = {3081: '695913205d996e363a5d58509c8ff494600dd171700642972c5c9a1f16565a67', 3085: 'a831da8231f649c1ea83cd6b497a9398561453027e1d01e193a1e8176668b0b3', 3096: '2e4d9668ff4ba78dff2274ae38a15fd0ebd77d980ee7f9f07849feaaca8c0fa1', 3101: 'c46b366a51b958a7c3ac33a6c5f6a2cba5a30ac0ee14788e8a5426b60febfae9', 3106: 'b2479b0312d1fd0e184cb40a41622b660a25ed4719415c9847c07d9fa2dcd1d0'}
SEED_BASE = 202610272017
OMITTED_MAXIMUM_SHAPES = {
3081: 'Exhaustive substitution is bounded to three wildcards and length 64; large probes use balanced-frequency/lexical proofs.',
3085: 'Prior unsolicited development snippet exposure retained. No global blindness; arbitrary maximum frequency profiles not exhaustively searched.',
3096: 'Finite maximum-shape probes, not all 2^100000 binary arrays; native performance unknown.',
3101: 'Finite maximum-shape probes, including exact count 5000050000, not all binary arrays.',
3106: 'Target enumeration is bounded to 20000 lexical targets and length 5 (complete for lengths <=3). Large expectations use independent cyclic-distance proofs.'}


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported exact identity or ordered argument shape')
    if pid == 3081:
        valid = text(args[0], string.ascii_lowercase+'?', 1, 100000)
    elif pid == 3085:
        valid = text(args[0], maximum=100000) and integer(args[1], 0, 100000)
    elif pid == 3096:
        valid = ints(args[0], 0, 1, 2, 100000)
    elif pid == 3101:
        valid = ints(args[0], 0, 1, 1, 100000)
    else:
        valid = text(args[0], maximum=100) and integer(args[1], 0, 2000)
    if not valid:
        raise ValueError('outside pinned full statement domain')


def _replace(s):
    positions = [i for i, c in enumerate(s) if c == '?']; best = None
    for letters in product(string.ascii_lowercase, repeat=len(positions)):
        chars = list(s)
        for i, c in zip(positions, letters): chars[i] = c
        value = sum(chars[i] == chars[j] for i in range(len(chars)) for j in range(i))
        item = (value, ''.join(chars))
        if best is None or item < best: best = item
    return best[1]


def _deletions(word, k):
    frequencies = tuple(Counter(word).values()); best = len(word)
    for retained in product(*(range(c+1) for c in frequencies)):
        nonzero = [c for c in retained if c]
        if not nonzero or max(nonzero)-min(nonzero) <= k:
            best = min(best, len(word)-sum(retained))
    return best


def _levels(a):
    points = [1 if x else -1 for x in a]
    for cut in range(1, len(a)):
        if sum(points[:cut]) > sum(points[cut:]): return cut
    return -1


def _alternating(a):
    return sum(all(a[i] != a[i+1] for i in range(left, right))
               for left in range(len(a)) for right in range(left, len(a)))


def _cyclic_targets(s, k):
    # Complete lexical enumeration for n<=3. The two public longer examples
    # have explicit early lexical feasible certificates inside this same cap.
    for target in islice(product(string.ascii_lowercase, repeat=len(s)), 20000):
        if sum(min(abs(ord(a)-ord(b)), 26-abs(ord(a)-ord(b))) for a, b in zip(s, target)) <= k:
            return ''.join(target)
    raise ValueError('bounded lexical target enumeration exhausted')


def expected(pid, args):
    validate(pid, args)
    if pid == 3081 and len(args[0]) <= 64 and args[0].count('?') <= 3:
        return _replace(args[0])
    if pid == 3085:
        work = 1
        for count in Counter(args[0]).values(): work *= count+1
        if work <= 50000: return _deletions(*args)
    if pid == 3096 and len(args[0]) <= 128:
        return _levels(args[0])
    if pid == 3101 and len(args[0]) <= 64:
        return _alternating(args[0])
    if pid == 3106 and len(args[0]) <= 5:
        return _cyclic_targets(*args)
    raise ValueError('bounded independent reference budget exceeded')


def public_examples(pid, raw):
    if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw) != STATEMENT_SHA256[pid]:
        raise ValueError('exact pinned statement bytes required')
    envelope = json.loads(raw)
    if type(envelope) is not dict or envelope.get('problem_id') != pid or type(envelope.get('web_result')) is not str:
        raise ValueError('invalid definition envelope')
    body = re.sub(r'^L\d+: ?', '', envelope['web_result'], flags=re.M)
    if f'{pid}. {TITLES[pid]}' not in body:
        raise ValueError('numeric identity/title mismatch')
    cases = []
    for match in re.finditer(r'Input:\s*(.*?)\n\s*Output:\s*([^\n]+)', body, re.S):
        call = ast.parse('f('+match[1].strip()+')', mode='eval').body
        if not isinstance(call, ast.Call) or call.args or tuple(x.arg for x in call.keywords) != PARAMETERS[pid]:
            raise ValueError('pinned ordered example parameters differ')
        args = [ast.literal_eval(x.value) for x in call.keywords]; answer = json.loads(match[2])
        if not q.exact(expected(pid, args), answer):
            raise ValueError('independent reference disagrees with public example')
        cases.append({'args': args, 'expected': answer, 'compare': 'return'})
    if len(cases) != EXAMPLE_COUNT[pid]:
        raise ValueError('complete pinned public examples required')
    return cases


def _generate_cases(pid, statement):
    cases = []; categories = []; seen = {}; rng = random.Random(SEED_BASE+pid); sentinel = object()
    def add(args, category, answer=sentinel):
        validate(pid, args); result = expected(pid, args) if answer is sentinel else answer; key = q.encoded(args)
        if key in seen:
            index = seen[key]
            if not q.exact(result, cases[index]['expected']): raise ValueError('conflicting duplicate expectation')
            if category not in categories[index].split('|'): categories[index] += '|'+category
            return
        seen[key] = len(cases); cases.append({'args': args, 'expected': result, 'compare': 'return'}); categories.append(category)
    for case in public_examples(pid, statement): add(case['args'], 'pinned_public_example', case['expected'])
    if pid == 3081:
        for n in range(1, 6):
            for chars in product('ab?', repeat=n):
                word = ''.join(chars)
                if word.count('?') <= 3: add([word], 'exhaustive_bounded_full_alphabet_substitutions')
        for _ in range(20):
            chars = list(''.join(rng.choices(string.ascii_lowercase, k=rng.randrange(1, 21))))
            for i in rng.sample(range(len(chars)), rng.randrange(min(3, len(chars))+1)): chars[i] = '?'
            add([''.join(chars)], 'seeded_full_alphabet_substitutions')
        # 100000 = 26*3846+4. Lexical tie-breaking puts the four excess
        # occurrences on a,b,c,d and sorts all inserted letters.
        balanced = ''.join(c*(3847 if c in 'abcd' else 3846) for c in string.ascii_lowercase)
        add(['?'*100000], 'analytic_maximum_balanced_lexical_assignment', balanced)
        add(['z'*100000], 'analytic_maximum_no_replacement', 'z'*100000)
        add(['?'*99999+'z'], 'analytic_maximum_fixed_final_z', balanced[:-1]+'z')
    elif pid == 3085:
        for n in range(1, 6):
            for chars in product('abc', repeat=n):
                for k in range(4): add([''.join(chars), k], 'exhaustive_small_retained_count_assignments')
        for _ in range(60):
            add([''.join(rng.choices('abcxyz', k=rng.randrange(1, 14))), rng.randrange(0, 14)], 'seeded_retained_count_assignments')
        add(['a'*100000, 0], 'analytic_maximum_single_frequency', 0)
        add(['a'*99999+'b', 0], 'analytic_maximum_remove_single_outlier', 1)
        add(['a'*40000+'b'*35000+'c'*25000, 5000], 'analytic_maximum_three_frequency_interval', 15000)
        add(['a'*99999+'b', 100000], 'analytic_maximum_k_no_deletion', 0)
    elif pid in (3096, 3101):
        for n in range(2 if pid == 3096 else 1, 13):
            for values in product((0, 1), repeat=n): add([list(values)], 'exhaustive_binary_subarray_or_split_enumeration')
        for _ in range(60):
            n = rng.randrange(2 if pid == 3096 else 1, 65)
            add([[rng.randrange(2) for _ in range(n)]], 'seeded_binary_boundaries')
        if pid == 3096:
            for values, answer in [([0]*100000, 1), ([1]*100000, 50001), ([1, 0]*50000, 1), ([0, 1]*50000, -1)]:
                add([values], 'analytic_maximum_strict_score_split', answer)
        else:
            add([[0]*100000], 'analytic_maximum_equal_bits', 100000)
            add([[0, 1]*50000], 'analytic_maximum_alternation_above_32_bit', 5000050000)
            add([[0, 1]*25000+[1, 0]*25000], 'analytic_maximum_two_alternating_runs', 2500050000)
    else:
        for letter in string.ascii_lowercase:
            for k in range(27): add([letter, k], 'exhaustive_single_letter_cyclic_distances')
        for pair in product(string.ascii_lowercase, repeat=2):
            for k in (0, 1, 2, 12, 13, 25, 26): add([''.join(pair), k], 'exhaustive_two_letter_lexical_target_enumeration')
        for _ in range(40): add([''.join(rng.choices(string.ascii_lowercase, k=3)), rng.randrange(40)], 'seeded_three_letter_lexical_targets')
        add(['z'*100, 100], 'analytic_maximum_one_step_wrap_everywhere', 'a'*100)
        add(['n'*100, 2000], 'analytic_maximum_budget_exceeds_all_distance', 'a'*100)
        add(['z'*100, 0], 'analytic_maximum_zero_budget', 'z'*100)
        add(['n'*100, 13], 'analytic_maximum_budget_spent_at_first_position', 'a'+'n'*99)
    return cases, categories


def expected_observation_bytes(batch, language):
    if language not in ('javascript', 'python'):
        raise ValueError('unsupported observer language')
    return (sum(len(q.encoded({'i': i, 'result': c['expected'], 'result_type': q.expected_type(c['expected'], language),
                              'args_before': c['args'], 'args_after': c['args'], 'alias_edges': []}))
                for i, c in enumerate(batch)) + len(q.encoded({'done': len(batch)})) + (language == 'python'))


def build_cases(pid, statement):
    cases, categories = _generate_cases(pid, statement)
    if len(cases) != CASE_COUNT.get(pid) or q.sha(q.encoded(cases)) != CASES_SHA256.get(pid):
        raise ValueError('frozen case population or bytes changed')
    if len(q.encoded(cases)) > q.MAX_FILE:
        raise ValueError('case file exceeds unchanged reader cap')
    for _, batch in q.batches(cases):
        if any(expected_observation_bytes(batch, language) > q.LIMITS['max_output_bytes'] for language in ('javascript', 'python')):
            raise ValueError('expected observations exceed unchanged output cap')
    return cases, categories
