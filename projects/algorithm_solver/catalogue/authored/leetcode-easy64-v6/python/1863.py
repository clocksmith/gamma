"""1863. Sum of All Subset XOR Totals (Easy).

Specification: https://leetcode.com/problems/sum-of-all-subset-xor-totals/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; OR is safe for the declared values 1..20; preserve nums."""
    combined = 0
    for value in nums:
        combined |= value
    # Each bit present in the input is set in exactly half of all subset XORs.
    return combined * (2 ** (len(nums) - 1))


class Solution:
    def subsetXORSum(self, nums: list[int]) -> int:
        return solve(nums)
