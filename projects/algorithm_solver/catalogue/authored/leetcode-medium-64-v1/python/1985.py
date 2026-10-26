"""1985. Find the Kth Largest Integer in the Array: sort decimal strings by length then lexical value without numeric conversion."""


def solve(nums: list[str], k: int) -> str:
    """O(n * L * log n) time and O(n) auxiliary space for maximum digit length L; inputs are read-only."""
    ordered = sorted(nums, key=lambda value: (len(value), value))
    return ordered[len(ordered) - k]


class Solution:
    def kthLargestNumber(self, nums: list[str], k: int) -> str:
        return solve(nums, k)
