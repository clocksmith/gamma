"""777. Swap Adjacent in LR String (Medium).

Specification: https://leetcode.com/problems/swap-adjacent-in-lr-string/description/
"""


def solve(start: str, end: str) -> bool:
    if len(start) != len(end):
        return False
    i = j = 0
    while i < len(start) and j < len(end):
        while i < len(start) and start[i] == 'X':
            i += 1
        while j < len(end) and end[j] == 'X':
            j += 1
        if i == len(start) and j == len(end):
            return True
        if i == len(start) or j == len(end):
            return False
        if start[i] != end[j]:
            return False
        if start[i] == 'L' and i < j:
            return False
        if start[i] == 'R' and i > j:
            return False
        i += 1
        j += 1
    while i < len(start) and start[i] == 'X':
        i += 1
    while j < len(end) and end[j] == 'X':
        j += 1
    return i == len(start) and j == len(end)


class Solution:
    def canTransform(self, start: str, end: str) -> bool:
        return solve(start, end)
