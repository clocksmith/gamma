"""2299. Strong Password Checker II (Easy).

Specification: https://leetcode.com/problems/strong-password-checker-ii/description/
"""


def solve(password: str) -> bool:
    """O(n) time, O(1) space; require four ASCII character categories and no equal adjacent characters."""
    if len(password) < 8:
        return False
    lowercase = False
    uppercase = False
    digit = False
    special = False
    symbols = '!@#$%^&*()-+'
    for index, character in enumerate(password):
        if index > 0 and character == password[index - 1]:
            return False
        if 'a' <= character <= 'z':
            lowercase = True
        elif 'A' <= character <= 'Z':
            uppercase = True
        elif '0' <= character <= '9':
            digit = True
        elif character in symbols:
            special = True
    return lowercase and uppercase and digit and special


class Solution:
    def strongPasswordCheckerII(self, password: str) -> bool:
        return solve(password)
