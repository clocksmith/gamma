"""713. Subarray Product Less Than K. Positive-input sliding window; count every valid suffix ending at each position."""

def solve(nums: list[int], k: int) -> int:
    if k <= 1:
        return 0
    left = answer = 0
    product = 1
    for right, value in enumerate(nums):
        product *= value
        while product >= k:
            product //= nums[left]
            left += 1
        answer += right - left + 1
    return answer


class Solution:
    def numSubarrayProductLessThanK(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
