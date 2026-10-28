"""1328. Break a Palindrome (Medium).

Specification: https://leetcode.com/problems/break-a-palindrome/description/
"""


def solve(palindrome):
    n = len(palindrome)
    if n == 1:
        return ""
    chars = list(palindrome)
    i = 0
    while i < n // 2 and chars[i] == "a":
        i += 1
    if i == n // 2:
        chars[n - 1] = "b"
    else:
        chars[i] = "a"
    return "".join(chars)


class Solution:
    def breakPalindrome(self, palindrome):
        return solve(palindrome)
