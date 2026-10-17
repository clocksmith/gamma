"""Versioned, input-bound corrections to imported development tests.

Raw files and historical receipts remain unchanged. No case is dropped, no
expected output is altered, and changed source cases fail closed. These two
inclusive ranges had upper endpoints equal to the array length, contrary to
the statement. Shortening them by one makes their original expected outputs
valid; a separate direct-count oracle checks every corrected case.
"""
import copy
import hashlib
import json


VOWEL_RANGE_CORRECTIONS = {
    60: ('a3052d4dcc401cc32ae356e59ce8d42c6869cb497e03cc37bc71a28498475660', 13),
    84: ('0a12d799565916603a8e9fed492a7f2bd4dfdf7007ce3d0a8c795b63724756cc', 3),
}


def apply(problem, tests):
    if problem.uid != 'lcd:2559':
        return tests
    if problem.slug != 'count-vowel-strings-in-ranges':
        raise ValueError('Test-correction problem identity changed')
    result = copy.deepcopy(tests)
    for index, (expected_hash, query_index) in VOWEL_RANGE_CORRECTIONS.items():
        if len(result) <= index:
            raise ValueError('Corrected source test set changed')
        case = result[index]
        if hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest() != expected_hash:
            raise ValueError('Corrected source test changed; re-audit required')
        words, queries = case['args']
        left, right = queries[query_index]
        if right != len(words) or not 0 <= left < right:
            raise ValueError('Expected range defect is absent')
        queries[query_index][1] -= 1
        oracle = []
        for left, right in queries:
            if not 0 <= left <= right < len(words):
                raise ValueError('Corrected query still violates constraints')
            oracle.append(sum(1 for i in range(left, right + 1)
                              if words[i][0] in 'aeiou' and words[i][-1] in 'aeiou'))
        if oracle != case['expected']:
            raise ValueError('Corrected input disagrees with independent direct-count oracle')
    return result
