"""760. Find Anagram Mappings (Easy).

Specification: https://leetcode.com/problems/find-anagram-mappings/description/
"""


def solve(nums1: list[int], nums2: list[int]) -> list[int]:
    index_by_value = {value: i for i, value in enumerate(nums2)}
    return [index_by_value[value] for value in nums1]


class Solution:
    def anagramMappings(self, nums1: list[int], nums2: list[int]) -> list[int]:
        return solve(nums1, nums2)
