"""810. Chalkboard XOR Game (Hard).

Specification: https://leetcode.com/problems/chalkboard-xor-game/description/
"""


def solve(nums: list[int]) -> bool:
    xor = 0
    for value in nums:
        xor ^= value
    return xor == 0 or len(nums) % 2 == 0


class Solution:
    def xorGame(self, nums: list[int]) -> bool:
        return solve(nums)
