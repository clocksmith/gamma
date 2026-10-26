"""1392. Longest Happy Prefix.

KMP prefix-function construction; O(n) time and O(n) space. Inputs are preserved.
"""

def solve(s: str) -> str:
    border = [0] * len(s)
    for index in range(1, len(s)):
        length = border[index - 1]
        while length and s[index] != s[length]:
            length = border[length - 1]
        if s[index] == s[length]:
            length += 1
        border[index] = length
    return s[:border[-1]] if s else ''


class Solution:
    def longestPrefix(self, s: str) -> str:
        return solve(s)
