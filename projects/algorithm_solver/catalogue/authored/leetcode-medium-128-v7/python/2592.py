"""2592. Maximize Greatness of an Array: greedily match each larger sorted value to the smallest unmatched value."""


def solve(nums: list[int]) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    ordered = sorted(nums)
    matched = 0
    for value in ordered:
        if value > ordered[matched]:
            matched += 1
    return matched


class Solution:
    def maximizeGreatness(self, nums: list[int]) -> int:
        return solve(nums)
