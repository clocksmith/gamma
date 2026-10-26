"""2465. Number of Distinct Averages (Easy).

Specification: https://leetcode.com/problems/number-of-distinct-averages/description/
"""


def solve(nums: list[int]) -> int:
    """O(n log n) time, O(n) space; count distinct extreme-pair sums rather than floating averages; preserve nums."""
    values = sorted(nums)
    sums = set()
    for index in range(len(values) // 2):
        sums.add(values[index] + values[-1 - index])
    return len(sums)


class Solution:
    def distinctAverages(self, nums: list[int]) -> int:
        return solve(nums)
