"""2179. Count Good Triplets in an Array."""


def solve(nums1: list[int], nums2: list[int]) -> int:
    """Permutation positions and a Fenwick prefix count; O(n log n) time and O(n) space. Inputs are preserved."""
    size = len(nums1)
    positions = [0] * size
    for index, value in enumerate(nums2):
        positions[value] = index
    tree = [0] * (size + 1)
    answer = 0
    for index, value in enumerate(nums1):
        position = positions[value]
        cursor = position
        earlier_smaller = 0
        while cursor:
            earlier_smaller += tree[cursor]
            cursor -= cursor & -cursor
        later_larger = size - 1 - position - (index - earlier_smaller)
        answer += earlier_smaller * later_larger
        cursor = position + 1
        while cursor <= size:
            tree[cursor] += 1
            cursor += cursor & -cursor
    return answer


class Solution:
    def goodTriplets(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
