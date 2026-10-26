"""2488. Count Subarrays With Median K. Combine signed balances on both sides of the unique median."""


def solve(nums: list[int], k: int) -> int:
    """O(n) time and O(n) space. Inputs are preserved."""
    pivot = nums.index(k)
    counts = {0: 1}
    balance = 0
    for index in range(pivot + 1, len(nums)):
        balance += 1 if nums[index] > k else -1
        counts[balance] = counts.get(balance, 0) + 1
    answer = counts.get(0, 0) + counts.get(1, 0)
    balance = 0
    for index in range(pivot - 1, -1, -1):
        balance += 1 if nums[index] > k else -1
        answer += counts.get(-balance, 0) + counts.get(1 - balance, 0)
    return answer


class Solution:
    def countSubarrays(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
