"""3304. Find the K-th Character in String Game I (Easy).

Specification: https://leetcode.com/problems/find-the-k-th-character-in-string-game-i/description/
"""


def solve(k: int) -> str:
    """O(log k) time, O(1) space; each set bit of k - 1 contributes one alphabet step."""
    index = k - 1
    shifts = 0
    while index > 0:
        shifts += index % 2
        index //= 2
    return chr(ord('a') + shifts % 26)


class Solution:
    def kthCharacter(self, k: int) -> str:
        return solve(k)
