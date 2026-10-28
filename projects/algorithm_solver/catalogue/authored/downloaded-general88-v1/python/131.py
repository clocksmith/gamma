"""131. Palindrome Partitioning (Medium).

Specification: https://leetcode.com/problems/palindrome-partitioning/description/
"""


def _is_palindrome(text):
    return text == text[::-1]


def solve(s: str) -> list[list[str]]:
    result = []

    def backtrack(start, current):
        if start == len(s):
            result.append(current[:])
            return
        for end in range(start + 1, len(s) + 1):
            part = s[start:end]
            if _is_palindrome(part):
                current.append(part)
                backtrack(end, current)
                current.pop()

    backtrack(0, [])
    return result


class Solution:
    def partition(self, s: str) -> list[list[str]]:
        return solve(s)
