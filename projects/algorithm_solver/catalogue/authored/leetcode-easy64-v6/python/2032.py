"""2032. Two Out of Three (Easy).

Specification: https://leetcode.com/problems/two-out-of-three/description/
"""


def solve(nums1: list[int], nums2: list[int], nums3: list[int]) -> list[int]:
    """O(total input length + 100) time, O(1) bounded-domain space besides the result; preserve inputs."""
    membership = [0] * 101
    for value in nums1:
        membership[value] |= 1
    for value in nums2:
        membership[value] |= 2
    for value in nums3:
        membership[value] |= 4
    result = []
    for value in range(1, 101):
        mask = membership[value]
        if mask & (mask - 1):
            result.append(value)
    return result


class Solution:
    def twoOutOfThree(self, nums1: list[int], nums2: list[int], nums3: list[int]) -> list[int]:
        return solve(nums1, nums2, nums3)
