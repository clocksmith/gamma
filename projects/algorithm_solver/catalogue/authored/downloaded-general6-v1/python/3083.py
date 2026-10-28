"""3083. Existence of a Substring in a String and Its Reverse (Easy).

Specification: https://leetcode.com/problems/existence-of-a-substring-in-a-string-and-its-reverse/description/
"""


def solve(s: str) -> bool:
    reversed_s = s[::-1]
    for i in range(len(s) - 1):
        if s[i:i + 2] in reversed_s:
            return True
    return False


class Solution:
    def isSubstringPresent(self, s: str) -> bool:
        return solve(s)
