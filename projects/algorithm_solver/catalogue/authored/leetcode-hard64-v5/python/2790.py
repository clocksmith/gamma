"""2790. Maximum Number of Groups With Increasing Length. Process increasing capacities and add at most one distinct-element group per value."""


def solve(usageLimits: list[int]) -> int:
    """O(n log n) time and O(n) space. Inputs are preserved."""
    available = 0
    groups = 0
    for limit in sorted(usageLimits):
        available += limit
        if available >= (groups + 1) * (groups + 2) // 2:
            groups += 1
    return groups


class Solution:
    def maxIncreasingGroups(self, usageLimits: list[int]) -> int:
        return solve(usageLimits)
