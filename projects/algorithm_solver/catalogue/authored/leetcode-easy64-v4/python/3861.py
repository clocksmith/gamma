"""3861. Minimum Capacity Box (Easy).

Specification: https://leetcode.com/problems/minimum-capacity-box/description/
"""


def solve(capacity: list[int], itemSize: int) -> int:
    """O(n) time, O(1) space; preserve capacity; equal capacities retain the earliest index."""
    result = -1
    for index, size in enumerate(capacity):
        if size >= itemSize and (result == -1 or size < capacity[result]):
            result = index
    return result


class Solution:
    def minimumIndex(self, capacity: list[int], itemSize: int) -> int:
        return solve(capacity, itemSize)
