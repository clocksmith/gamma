"""3350. Adjacent Increasing Subarrays Detection II (Medium).

Specification: https://leetcode.com/problems/adjacent-increasing-subarrays-detection-ii/description/
"""


def solve(nums: list[int]) -> int:
    cnt = 1
    precnt = 0
    ans = 0
    for i in range(1, len(nums)):
        if nums[i] > nums[i - 1]:
            cnt += 1
        else:
            precnt, cnt = cnt, 1
        ans = max(ans, min(precnt, cnt), cnt // 2)
    return ans


class Solution:
    def maxIncreasingSubarrays(self, nums: list[int]) -> int:
        return solve(nums)
