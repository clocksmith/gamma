"""2856. Minimum Array Length After Pair Removals: leave only the unavoidable majority excess or the total-length parity."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space for the sorted input; inputs are read-only."""
    largest = run = 0
    previous = None
    for value in nums:
        run = run + 1 if value == previous else 1
        largest = max(largest, run)
        previous = value
    return max(len(nums) % 2, 2 * largest - len(nums))


class Solution:
    def minLengthAfterRemovals(self, nums: list[int]) -> int:
        return solve(nums)
