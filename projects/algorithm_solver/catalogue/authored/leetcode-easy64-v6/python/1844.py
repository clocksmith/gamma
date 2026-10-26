"""1844. Replace All Digits with Characters (Easy).

Specification: https://leetcode.com/problems/replace-all-digits-with-characters/description/
"""


def solve(s: str) -> str:
    """O(n) time and space; each odd-index digit shifts the preceding ASCII letter."""
    result = list(s)
    for index in range(1, len(s), 2):
        offset = ord(s[index]) - ord('0')
        result[index] = chr(ord(s[index - 1]) + offset)
    return ''.join(result)


class Solution:
    def replaceDigits(self, s: str) -> str:
        return solve(s)
