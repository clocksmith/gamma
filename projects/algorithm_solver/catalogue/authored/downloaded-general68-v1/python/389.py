"""389. Find the Difference (Easy).

Specification: https://leetcode.com/problems/find-the-difference/description/
"""


def solve(s: str, t: str) -> str:
    xor = 0
    for ch in s:
        xor ^= ord(ch)
    for ch in t:
        xor ^= ord(ch)
    return chr(xor)


class Solution:
    def findTheDifference(self, s: str, t: str) -> str:
        return solve(s, t)
