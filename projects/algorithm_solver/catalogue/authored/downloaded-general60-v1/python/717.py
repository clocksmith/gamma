"""717. 1-bit and 2-bit Characters (Easy).

Specification: https://leetcode.com/problems/1-bit-and-2-bit-characters/description/
"""


def solve(bits: list[int]) -> bool:
    i = 0
    while i < len(bits) - 1:
        i += 2 if bits[i] == 1 else 1
    return i == len(bits) - 1


class Solution:
    def isOneBitCharacter(self, bits: list[int]) -> bool:
        return solve(bits)
