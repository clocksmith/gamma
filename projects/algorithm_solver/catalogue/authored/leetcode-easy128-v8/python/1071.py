"""1071. Greatest Common Divisor of Strings (Easy).

Specification: https://leetcode.com/problems/greatest-common-divisor-of-strings/description/
"""


def solve(str1: str, str2: str) -> str:
    """O(n + m) time and space; concatenation compatibility plus the GCD of lengths."""
    if str1 + str2 != str2 + str1:
        return ''
    first, second = len(str1), len(str2)
    while second:
        first, second = second, first % second
    return str1[:first]


class Solution:
    def gcdOfStrings(self, str1: str, str2: str) -> str:
        return solve(str1, str2)
