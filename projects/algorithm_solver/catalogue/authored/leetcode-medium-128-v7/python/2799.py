"""2799. Count Complete Subarrays in an Array: shrink each complete window and count every valid earlier starting position."""


def solve(nums: list[int]) -> int:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    required = len(set(nums))
    counts = {}
    left = result = 0
    for value in nums:
        counts[value] = counts.get(value, 0) + 1
        while len(counts) == required:
            removed = nums[left]
            counts[removed] -= 1
            if counts[removed] == 0:
                del counts[removed]
            left += 1
        result += left
    return result


class Solution:
    def countCompleteSubarrays(self, nums: list[int]) -> int:
        return solve(nums)
