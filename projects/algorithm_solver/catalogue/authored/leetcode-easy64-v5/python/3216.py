"""3216. Lexicographically Smallest String After a Swap (Easy).

Specification: https://leetcode.com/problems/lexicographically-smallest-string-after-a-swap/description/
"""


def solve(s: str) -> str:
    """O(n) time and space; perform only the first improving adjacent same-parity swap."""
    digits = list(s)
    for index in range(len(digits) - 1):
        if digits[index] > digits[index + 1] and (ord(digits[index]) - ord(digits[index + 1])) % 2 == 0:
            digits[index], digits[index + 1] = digits[index + 1], digits[index]
            break
    return ''.join(digits)


class Solution:
    def getSmallestString(self, s: str) -> str:
        return solve(s)
