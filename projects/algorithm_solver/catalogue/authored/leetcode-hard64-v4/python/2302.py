"""2302. Count Subarrays With Score Less Than K."""


def solve(nums: list[int], k: int) -> int:
    """Positive-value sliding window; O(n) time and O(1) auxiliary space. Inputs are preserved."""
    left = 0
    total = 0
    answer = 0
    for right, value in enumerate(nums):
        total += value
        while left <= right and total * (right - left + 1) >= k:
            total -= nums[left]
            left += 1
        answer += right - left + 1
    return answer


class Solution:
    def countSubarrays(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
