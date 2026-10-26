"""2401. Longest Nice Subarray: maintain a sliding window with disjoint set bits."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space for values below 2^30; inputs are read-only."""
    mask = left = answer = 0
    for right, value in enumerate(nums):
        while mask & value:
            # Disjoint bits in the valid window make XOR an exact removal.
            mask ^= nums[left]
            left += 1
        mask |= value
        answer = max(answer, right - left + 1)
    return answer


class Solution:
    def longestNiceSubarray(self, nums: list[int]) -> int:
        return solve(nums)
