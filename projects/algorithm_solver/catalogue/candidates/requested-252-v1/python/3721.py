"""3721. Longest Balanced Subarray II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/longest-balanced-subarray-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3721.Longest%20Balanced%20Subarray%20II/README_EN.md
Complexity: O(n log n) time; O(n) space.
Inputs preserved. Balance across adjacent candidate starts changes by at most one; min/max pruning locates an actual zero.
"""

from __future__ import annotations

def solve(nums):
    n = len(nums)
    minimum = [0] * (4 * n)
    maximum = [0] * (4 * n)
    lazy = [0] * (4 * n)
    def apply(node, change):
        minimum[node] += change
        maximum[node] += change
        lazy[node] += change
    def push(node):
        if lazy[node]:
            apply(node * 2, lazy[node])
            apply(node * 2 + 1, lazy[node])
            lazy[node] = 0
    def update(node, left, right, begin, end, change):
        if begin <= left and right <= end:
            apply(node, change)
            return
        push(node)
        middle = (left + right) // 2
        if begin <= middle:
            update(node * 2, left, middle, begin, end, change)
        if end > middle:
            update(node * 2 + 1, middle + 1, right, begin, end, change)
        minimum[node] = min(minimum[node * 2], minimum[node * 2 + 1])
        maximum[node] = max(maximum[node * 2], maximum[node * 2 + 1])
    def earliest_zero(node, left, right, end):
        if left > end or minimum[node] > 0 or maximum[node] < 0:
            return -1
        if left == right:
            return left
        push(node)
        middle = (left + right) // 2
        answer = earliest_zero(node * 2, left, middle, end)
        return answer if answer != -1 else earliest_zero(node * 2 + 1, middle + 1, right, end)
    last = {}
    answer = 0
    for right, value in enumerate(nums):
        update(1, 0, n - 1, last.get(value, -1) + 1, right, 1 if value % 2 == 0 else -1)
        last[value] = right
        left = earliest_zero(1, 0, n - 1, right)
        if left != -1:
            answer = max(answer, right - left + 1)
    return answer


class Solution:
    def longestBalanced(self, nums):
        return solve(nums)
