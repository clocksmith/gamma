"""3159. Find Occurrences of an Element in an Array: index matching positions once and answer one-based occurrence queries."""


def solve(nums: list[int], queries: list[int], x: int) -> list[int]:
    """O(n + q) time and O(n + q) space including output; inputs are read-only."""
    positions = [index for index, value in enumerate(nums) if value == x]
    return [positions[query - 1] if query <= len(positions) else -1 for query in queries]


class Solution:
    def occurrencesOfElement(self, nums: list[int], queries: list[int], x: int) -> list[int]:
        return solve(nums, queries, x)
