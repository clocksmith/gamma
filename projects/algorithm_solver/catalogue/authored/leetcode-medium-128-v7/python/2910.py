"""2910. Minimum Number of Groups to Create a Valid Assignment: try descending base group sizes and express each frequency using adjacent sizes."""
from collections import Counter


def solve(nums: list[int]) -> int:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    frequencies = list(Counter(nums).values())
    for small in range(min(frequencies), 0, -1):
        total = 0
        for frequency in frequencies:
            groups = (frequency + small) // (small + 1)
            if groups * small > frequency:
                break
            total += groups
        else:
            return total
    return len(nums)


class Solution:
    def minGroupsForValidAssignment(self, nums: list[int]) -> int:
        return solve(nums)
