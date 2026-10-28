"""421. Maximum XOR of Two Numbers in an Array (Medium).

Specification: https://leetcode.com/problems/maximum-xor-of-two-numbers-in-an-array/description/
"""


def solve(nums: list[int]) -> int:
    max_xor = 0
    mask = 0
    for bit in range(30, -1, -1):
        mask |= (1 << bit)
        prefixes = {value & mask for value in nums}
        candidate = max_xor | (1 << bit)
        found = False
        for prefix in prefixes:
            if (prefix ^ candidate) in prefixes:
                found = True
                break
        if found:
            max_xor = candidate
    return max_xor


class Solution:
    def findMaximumXOR(self, nums: list[int]) -> int:
        return solve(nums)
