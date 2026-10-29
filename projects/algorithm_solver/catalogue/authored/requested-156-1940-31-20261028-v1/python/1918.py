"""Original frontend 1918 variant; qualification unknown."""


def solve(nums, k: int) -> int:
    lo, hi = min(nums), sum(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        cnt = 0
        cur = 0
        left = 0
        for right, x in enumerate(nums):
            cur += x
            while cur > mid:
                cur -= nums[left]
                left += 1
            cnt += right - left + 1
        if cnt >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


kthSmallestSubarraySum = solve


class Solution:
    def kthSmallestSubarraySum(self, nums, k: int) -> int:
        return solve(nums, k)
