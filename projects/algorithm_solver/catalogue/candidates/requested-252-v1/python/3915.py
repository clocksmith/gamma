"""3915. Maximum Sum of Alternating Subsequence With Distance at Least K.

Specification: https://leetcode.com/problems/maximum-sum-of-alternating-subsequence-with-distance-at-least-k/description/
"""

from __future__ import annotations


def solve(nums: list[int], k: int) -> int:
    """O(n log n) time, O(n) space; activate only predecessors at distance at least k. Inputs are preserved."""
    values = sorted(set(nums))
    ranks = {value: index + 1 for index, value in enumerate(values)}
    size = len(values)
    lower = [0] * (size + 1)
    upper = [0] * (size + 1)
    up = [0] * len(nums)
    down = [0] * len(nums)

    def update(tree, index, value):
        while index <= size:
            tree[index] = max(tree[index], value)
            index += index & -index

    def prefix(tree, index):
        value = 0
        while index:
            value = max(value, tree[index])
            index -= index & -index
        return value

    answer = 0
    for index, value in enumerate(nums):
        if index >= k:
            previous = index - k
            rank = ranks[nums[previous]]
            update(lower, rank, down[previous])
            update(upper, size - rank + 1, up[previous])
        rank = ranks[value]
        up[index] = value + prefix(lower, rank - 1)
        down[index] = value + prefix(upper, size - rank)
        answer = max(answer, up[index], down[index])
    return answer

# Native judge method name is not established; canonical solve is the supported entry point.
