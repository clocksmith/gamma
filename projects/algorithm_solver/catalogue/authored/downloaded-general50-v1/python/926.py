"""926. Flip String to Monotone Increasing (Medium).

Specification: https://leetcode.com/problems/flip-string-to-monotone-increasing/description/
"""


def solve(s: str) -> int:
    flips = 0
    ones = 0
    for ch in s:
        if ch == '1':
            ones += 1
        else:
            flips = min(flips + 1, ones)
    return flips


class Solution:
    def minFlipsMonoIncr(self, s: str) -> int:
        return solve(s)
