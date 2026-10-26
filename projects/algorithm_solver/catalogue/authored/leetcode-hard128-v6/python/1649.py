"""1649. Create Sorted Array through Instructions.

Coordinate compression and Fenwick counts of smaller and larger entries; O(n log n) time, O(n) space. Inputs are preserved.
"""

from bisect import bisect_left


def solve(instructions: list[int]) -> int:
    values = sorted(set(instructions))
    tree = [0] * (len(values) + 1)

    def prefix(index):
        result = 0
        while index:
            result += tree[index]
            index -= index & -index
        return result

    answer = 0
    for inserted, value in enumerate(instructions):
        rank = bisect_left(values, value) + 1
        answer = (answer + min(prefix(rank - 1), inserted - prefix(rank))) % 1_000_000_007
        index = rank
        while index < len(tree):
            tree[index] += 1
            index += index & -index
    return answer


class Solution:
    def createSortedArray(self, instructions: list[int]) -> int:
        return solve(instructions)
