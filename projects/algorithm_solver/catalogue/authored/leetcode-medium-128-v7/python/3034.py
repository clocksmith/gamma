"""3034. Number of Subarrays That Match a Pattern I: check each candidate window against its required adjacent comparison signs."""


def solve(nums: list[int], pattern: list[int]) -> int:
    """O(n * m) time and O(1) auxiliary space, where m is the pattern length; inputs are read-only."""
    total = 0
    for start in range(len(nums) - len(pattern)):
        for offset, required in enumerate(pattern):
            left, right = nums[start + offset], nums[start + offset + 1]
            observed = (right > left) - (right < left)
            if observed != required:
                break
        else:
            total += 1
    return total


class Solution:
    def countMatchingSubarrays(self, nums: list[int], pattern: list[int]) -> int:
        return solve(nums, pattern)
