"""350. Intersection of Two Arrays II (Easy).

Specification: https://leetcode.com/problems/intersection-of-two-arrays-ii/description/
"""


def solve(nums1: list[int], nums2: list[int]) -> list[int]:
    counts = {}
    for value in nums1:
        counts[value] = counts.get(value, 0) + 1
    result = []
    for value in nums2:
        if counts.get(value, 0) > 0:
            result.append(value)
            counts[value] -= 1
    return sorted(result)


class Solution:
    def intersect(self, nums1: list[int], nums2: list[int]) -> list[int]:
        return solve(nums1, nums2)
