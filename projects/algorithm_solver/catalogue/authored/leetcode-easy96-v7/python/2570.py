"""2570. Merge Two 2D Arrays by Summing Values (Easy).

Specification: https://leetcode.com/problems/merge-two-2d-arrays-by-summing-values/description/
"""


def solve(nums1: list[list[int]], nums2: list[list[int]]) -> list[list[int]]:
    """O(n + m) time and result space; merge sorted IDs into fresh pairs; preserve inputs and row identities."""
    result = []
    first = 0
    second = 0
    while first < len(nums1) or second < len(nums2):
        if second == len(nums2) or (first < len(nums1) and nums1[first][0] < nums2[second][0]):
            result.append([nums1[first][0], nums1[first][1]])
            first += 1
        elif first == len(nums1) or nums2[second][0] < nums1[first][0]:
            result.append([nums2[second][0], nums2[second][1]])
            second += 1
        else:
            result.append([nums1[first][0], nums1[first][1] + nums2[second][1]])
            first += 1
            second += 1
    return result


class Solution:
    def mergeArrays(self, nums1: list[list[int]], nums2: list[list[int]]) -> list[list[int]]:
        return solve(nums1, nums2)
