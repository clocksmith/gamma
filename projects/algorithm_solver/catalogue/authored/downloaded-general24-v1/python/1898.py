"""1898. Maximum Number of Removable Characters (Medium).

Specification: https://leetcode.com/problems/maximum-number-of-removable-characters/description/
"""


def _is_subsequence(s, p, removed):
    j = 0
    for i, ch in enumerate(s):
        if j >= len(p):
            break
        if i in removed:
            continue
        if ch == p[j]:
            j += 1
    return j == len(p)


def solve(s: str, p: str, removable: list[int]) -> int:
    left, right, best = 0, len(removable), 0
    while left <= right:
        mid = (left + right) // 2
        removed = set(removable[:mid])
        if _is_subsequence(s, p, removed):
            best = mid
            left = mid + 1
        else:
            right = mid - 1
    return best


class Solution:
    def maximumRemovals(self, s: str, p: str, removable: list[int]) -> int:
        return solve(s, p, removable)
