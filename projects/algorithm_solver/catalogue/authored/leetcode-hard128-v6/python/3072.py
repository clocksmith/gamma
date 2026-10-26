"""3072. Distribute Elements Into Two Arrays II.

Two Fenwick trees count strictly larger prior values; O(n log n) time and O(n) space. Inputs are preserved and the result is fresh.
"""

from bisect import bisect_left


def solve(nums: list[int]) -> list[int]:
    values = sorted(set(nums))
    trees = [[0] * (len(values) + 1) for _ in range(2)]
    arrays = [[], []]

    def prefix(tree, index):
        result = 0
        while index:
            result += tree[index]
            index -= index & -index
        return result

    for position, value in enumerate(nums):
        rank = bisect_left(values, value) + 1
        if position < 2:
            chosen = position
        else:
            first = len(arrays[0]) - prefix(trees[0], rank)
            second = len(arrays[1]) - prefix(trees[1], rank)
            chosen = 0 if first > second or first == second and len(arrays[0]) <= len(arrays[1]) else 1
        arrays[chosen].append(value)
        index = rank
        while index < len(trees[chosen]):
            trees[chosen][index] += 1
            index += index & -index
    return arrays[0] + arrays[1]


class Solution:
    def resultArray(self, nums: list[int]) -> list[int]:
        return solve(nums)
