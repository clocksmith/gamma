"""3917. Count Indices With Opposite Parity (Easy).

Specification: https://leetcode.com/problems/count-indices-with-opposite-parity/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n) time, O(1) auxiliary space beyond the output; count only later indices; preserve nums."""
    result = [0] * len(nums)
    counts = [0, 0]
    for index in range(len(nums) - 1, -1, -1):
        parity = nums[index] % 2
        result[index] = counts[1 - parity]
        counts[parity] += 1
    return result


class Solution:
    def countOppositeParity(self, nums: list[int]) -> list[int]:
        return solve(nums)
