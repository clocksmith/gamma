"""1869. Longer Contiguous Segments of Ones than Zeros (Easy).

Specification: https://leetcode.com/problems/longer-contiguous-segments-of-ones-than-zeros/description/
"""


def _longest_run(s, target):
    best = 0
    current = 0
    for ch in s:
        if ch == target:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def solve(s: str) -> bool:
    return _longest_run(s, '1') > _longest_run(s, '0')


class Solution:
    def checkZeroOnes(self, s: str) -> bool:
        return solve(s)
