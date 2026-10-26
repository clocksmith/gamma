"""2411. Smallest Subarrays With Maximum Bitwise OR: scan backwards and retain the nearest occurrence of every possible set bit."""


def solve(nums: list[int]) -> list[int]:
    """O(30 * n) time and O(n) output space with O(1) auxiliary space; inputs are read-only."""
    nearest = [-1] * 30
    answer = [1] * len(nums)
    for index in range(len(nums) - 1, -1, -1):
        end = index
        for bit in range(30):
            if nums[index] & (1 << bit):
                nearest[bit] = index
            end = max(end, nearest[bit])
        answer[index] = end - index + 1
    return answer


class Solution:
    def smallestSubarrays(self, nums: list[int]) -> list[int]:
        return solve(nums)
