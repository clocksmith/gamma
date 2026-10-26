"""2215. Find the Difference of Two Arrays (Easy).

Specification: https://leetcode.com/problems/find-the-difference-of-two-arrays/description/
"""


def solve(nums1: list[int], nums2: list[int]) -> list[list[int]]:
    """O(n + m) expected time and space; distinct results in first-occurrence order; preserve inputs."""
    first = dict.fromkeys(nums1)
    second = dict.fromkeys(nums2)
    first_only = [value for value in first if value not in second]
    second_only = [value for value in second if value not in first]
    return [first_only, second_only]


class Solution:
    def findDifference(self, nums1: list[int], nums2: list[int]) -> list[list[int]]:
        return solve(nums1, nums2)
