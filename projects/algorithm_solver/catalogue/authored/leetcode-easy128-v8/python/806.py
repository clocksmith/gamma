"""806. Number of Lines To Write String (Easy).

Specification: https://leetcode.com/problems/number-of-lines-to-write-string/description/
"""


def solve(widths: list[int], s: str) -> list[int]:
    """O(n) time, O(1) space; wrap before a letter would exceed 100 units."""
    lines = 1
    used = 0
    for character in s:
        width = widths[ord(character) - 97]
        if used + width > 100:
            lines += 1
            used = 0
        used += width
    return [lines, used]


class Solution:
    def numberOfLines(self, widths: list[int], s: str) -> list[int]:
        return solve(widths, s)
