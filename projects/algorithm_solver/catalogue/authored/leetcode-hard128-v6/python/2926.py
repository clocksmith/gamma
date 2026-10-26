"""2926. Maximum Balanced Subsequence Sum.

Fenwick maximum over compressed value-minus-index keys; O(n log n) time, O(n) space. Inputs are preserved.
"""

from bisect import bisect_left


def solve(nums: list[int]) -> int:
    keys = sorted(set(value - index for index, value in enumerate(nums)))
    tree = [0] * (len(keys) + 1)
    answer = max(nums)
    for position, value in enumerate(nums):
        rank = bisect_left(keys, value - position) + 1
        index, previous = rank, 0
        while index:
            previous = max(previous, tree[index])
            index -= index & -index
        current = previous + value
        answer = max(answer, current)
        index = rank
        while index < len(tree):
            tree[index] = max(tree[index], current)
            index += index & -index
    return answer


class Solution:
    def maxBalancedSubsequenceSum(self, nums: list[int]) -> int:
        return solve(nums)
