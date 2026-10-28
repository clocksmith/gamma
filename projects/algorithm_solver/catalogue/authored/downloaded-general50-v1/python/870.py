"""870. Advantage Shuffle (Medium).

Specification: https://leetcode.com/problems/advantage-shuffle/description/
"""


def solve(nums1: list[int], nums2: list[int]) -> list[int]:
    ordered = sorted(nums1)
    order = sorted(range(len(nums2)), key=lambda i: nums2[i])
    result = [0] * len(nums1)
    left, right = 0, len(ordered) - 1
    for k in range(len(order) - 1, -1, -1):
        idx = order[k]
        if ordered[right] > nums2[idx]:
            result[idx] = ordered[right]
            right -= 1
        else:
            result[idx] = ordered[left]
            left += 1
    return result


class Solution:
    def advantageCount(self, nums1: list[int], nums2: list[int]) -> list[int]:
        return solve(nums1, nums2)
