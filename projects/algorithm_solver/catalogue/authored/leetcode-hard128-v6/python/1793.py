"""1793. Maximum Score of a Good Subarray.

Expand from k toward the larger boundary value; O(n) time, O(1) space. Inputs are preserved.
"""

def solve(nums: list[int], k: int) -> int:
    left = right = k
    minimum = answer = nums[k]
    while left > 0 or right + 1 < len(nums):
        if left == 0 or right + 1 < len(nums) and nums[right + 1] > nums[left - 1]:
            right += 1
            minimum = min(minimum, nums[right])
        else:
            left -= 1
            minimum = min(minimum, nums[left])
        answer = max(answer, minimum * (right - left + 1))
    return answer


class Solution:
    def maximumScore(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
