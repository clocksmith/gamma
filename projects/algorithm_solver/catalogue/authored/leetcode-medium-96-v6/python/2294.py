"""2294. Partition Array Such That Maximum Difference Is K: start each sorted group with the smallest value not yet covered."""


def solve(nums: list[int], k: int) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    ordered = sorted(nums)
    if not ordered:
        return 0
    groups = 1
    smallest = ordered[0]
    for value in ordered:
        if value - smallest > k:
            groups += 1
            smallest = value
    return groups


class Solution:
    def partitionArray(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
