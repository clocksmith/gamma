"""3309. Maximum Possible Number by Binary Concatenation (Medium).

Specification: https://leetcode.com/problems/maximum-possible-number-by-binary-concatenation/description/
"""


def solve(nums: list[int]) -> int:
    import itertools
    bins = [bin(x)[2:] for x in nums]
    best = 0
    for p in itertools.permutations(range(3)):
        val = int(''.join(bins[i] for i in p), 2)
        best = max(best, val)
    return best


class Solution:
    def maxGoodNumber(self, nums: list[int]) -> int:
        return solve(nums)
