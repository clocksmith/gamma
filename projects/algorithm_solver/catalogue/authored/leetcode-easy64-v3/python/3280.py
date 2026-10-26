"""3280. Convert Date to Binary (Easy).

Specification: https://leetcode.com/problems/convert-date-to-binary/description/
"""


def solve(date: str) -> str:
    """O(1) time and space for the bounded date format; omit binary leading zeros."""
    parts = date.split('-')
    return '-'.join(format(int(part), 'b') for part in parts)


class Solution:
    def convertDateToBinary(self, date: str) -> str:
        return solve(date)
