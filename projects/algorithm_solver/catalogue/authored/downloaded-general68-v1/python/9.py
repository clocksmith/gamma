"""9. Palindrome Number (Easy).

Specification: https://leetcode.com/problems/palindrome-number/description/
"""


def solve(x: int) -> bool:
    if x < 0:
        return False
    reversed_value = 0
    value = x
    while value != 0:
        reversed_value = reversed_value * 10 + (value % 10)
        value //= 10
    return reversed_value == x


class Solution:
    def isPalindrome(self, x: int) -> bool:
        return solve(x)
