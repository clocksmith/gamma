"""1556. Thousand Separator (Easy).

Specification: https://leetcode.com/problems/thousand-separator/description/
"""


def solve(n: int) -> str:
    """O(d) time and space; format decimal groups without locale settings."""
    digits = str(n)
    groups = []
    for end in range(len(digits), 0, -3):
        groups.append(digits[max(0, end - 3):end])
    groups.reverse()
    return '.'.join(groups)


class Solution:
    def thousandSeparator(self, n: int) -> str:
        return solve(n)
