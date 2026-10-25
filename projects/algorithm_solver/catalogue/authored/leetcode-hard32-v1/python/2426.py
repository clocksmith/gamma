"""2426. Number of Pairs Satisfying Inequality."""

from bisect import bisect_left, bisect_right


def solve(nums1: list[int], nums2: list[int], diff: int) -> int:
    """O(n log n) time, O(n) space; query previous differences with a Fenwick tree."""
    values = [first - second for first, second in zip(nums1, nums2)]
    ordered = sorted(set(values))
    tree = [0] * (len(ordered) + 1)
    answer = 0
    for value in values:
        index = bisect_right(ordered, value + diff)
        while index:
            answer += tree[index]
            index -= index & -index
        index = bisect_left(ordered, value) + 1
        while index < len(tree):
            tree[index] += 1
            index += index & -index
    return answer


class Solution:
    def numberOfPairs(self, nums1: list[int], nums2: list[int], diff: int) -> int:
        return solve(nums1, nums2, diff)
