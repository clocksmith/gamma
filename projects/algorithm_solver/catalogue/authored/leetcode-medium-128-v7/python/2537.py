"""2537. Count the Number of Good Subarrays: count equal pairs in a window and accumulate all valid left endpoints."""


def solve(nums: list[int], k: int) -> int:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    counts = {}
    pairs = left = total = 0
    for value in nums:
        pairs += counts.get(value, 0)
        counts[value] = counts.get(value, 0) + 1
        while pairs >= k:
            removed = nums[left]
            counts[removed] -= 1
            pairs -= counts[removed]
            left += 1
        total += left
    return total


class Solution:
    def countGood(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
