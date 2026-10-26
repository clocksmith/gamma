"""1537. Get the Maximum Score: two-pointer accumulation between shared values; O(n+m) time and O(1) space."""


def solve(nums1: list[int], nums2: list[int]) -> int:
    first = second = 0
    first_sum = second_sum = total = 0
    while first < len(nums1) or second < len(nums2):
        if second == len(nums2) or (first < len(nums1) and nums1[first] < nums2[second]):
            first_sum += nums1[first]
            first += 1
        elif first == len(nums1) or nums2[second] < nums1[first]:
            second_sum += nums2[second]
            second += 1
        else:
            total += max(first_sum, second_sum) + nums1[first]
            first_sum = second_sum = 0
            first += 1
            second += 1
    return (total + max(first_sum, second_sum)) % 1_000_000_007


class Solution:
    def maxSum(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
