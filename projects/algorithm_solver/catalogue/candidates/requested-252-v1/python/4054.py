"""4054. Count Shadow Pairs I.

Specification: https://leetcode.com/problems/count-shadow-pairs-i/description/
"""

from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) time and space; active prefix minima grouped by equal value. Inputs are preserved."""
    stack = []
    active = answer = 0
    for value in nums:
        while stack and stack[-1][0] > value:
            active -= stack.pop()[1]
        equal = stack[-1][1] if stack and stack[-1][0] == value else 0
        answer += active - equal
        if equal:
            stack[-1][1] += 1
        else:
            stack.append([value, 1])
        active += 1
    return answer

# Native judge method name is not established; canonical solve is the supported entry point.
