"""680. Valid Palindrome II (Easy).

Specification: https://leetcode.com/problems/valid-palindrome-ii/description/
"""


def _is_palindrome_range(s, left, right):
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    return True


def solve(s: str) -> bool:
    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            return _is_palindrome_range(s, left + 1, right) or _is_palindrome_range(s, left, right - 1)
        left += 1
        right -= 1
    return True


class Solution:
    def validPalindrome(self, s: str) -> bool:
        return solve(s)
