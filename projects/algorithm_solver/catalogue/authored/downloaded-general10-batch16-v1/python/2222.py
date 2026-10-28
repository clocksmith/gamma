"""2222. Number of Ways to Select Buildings (Medium).

Specification: https://leetcode.com/problems/number-of-ways-to-select-buildings/description/
"""


def solve(s: str) -> int:
    total = [0, 0]
    for ch in s:
        total[1 if ch == '1' else 0] += 1
    left = [0, 0]
    right = total[:]
    ans = 0
    for ch in s:
        x = 1 if ch == '1' else 0
        right[x] -= 1
        ans += left[1 - x] * right[1 - x]
        left[x] += 1
    return ans


class Solution:
    def numberOfWays(self, s) -> object:
        return solve(s)
