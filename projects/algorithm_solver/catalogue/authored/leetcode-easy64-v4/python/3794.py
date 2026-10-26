"""3794. Reverse String Prefix (Easy).

Specification: https://leetcode.com/problems/reverse-string-prefix/description/
"""


def solve(s: str, k: int) -> str:
    """O(n) time and space; reverse exactly the first k lowercase ASCII characters."""
    return s[:k][::-1] + s[k:]


class Solution:
    def reversePrefix(self, s: str, k: int) -> str:
        return solve(s, k)
