"""3740. Minimum Distance Between Three Equal Elements I (Easy).

Specification: https://leetcode.com/problems/minimum-distance-between-three-equal-elements-i/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) expected time and space; consecutive occurrences minimize twice the endpoint span."""
    positions = {}
    result = float('inf')
    for index, value in enumerate(nums):
        if value not in positions:
            positions[value] = []
        occurrences = positions[value]
        occurrences.append(index)
        if len(occurrences) >= 3:
            result = min(result, 2 * (index - occurrences[-3]))
    return -1 if result == float('inf') else result


class Solution:
    def minimumDistance(self, nums: list[int]) -> int:
        return solve(nums)
