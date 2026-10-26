"""1945. Sum of Digits of String After Convert (Easy).

Specification: https://leetcode.com/problems/sum-of-digits-of-string-after-convert/description/
"""


def solve(s: str, k: int) -> int:
    """O(n + k log(n + 1)) time, O(1) space; never construct the large encoded integer."""
    total = 0
    for character in s:
        position = ord(character) - ord('a') + 1
        total += position // 10 + position % 10
    for step in range(1, k):
        remaining = total
        total = 0
        while remaining > 0:
            total += remaining % 10
            remaining //= 10
    return total


class Solution:
    def getLucky(self, s: str, k: int) -> int:
        return solve(s, k)
