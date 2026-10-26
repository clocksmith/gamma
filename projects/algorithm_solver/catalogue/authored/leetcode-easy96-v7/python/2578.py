"""2578. Split With Minimum Sum (Easy).

Specification: https://leetcode.com/problems/split-with-minimum-sum/description/
"""


def solve(num: int) -> int:
    """O(d log d) time, O(d) space; distribute sorted digits alternately to minimize place values."""
    digits = sorted(str(num))
    parts = [0, 0]
    for index, digit in enumerate(digits):
        part = index % 2
        parts[part] = parts[part] * 10 + int(digit)
    return parts[0] + parts[1]


class Solution:
    def splitNum(self, num: int) -> int:
        return solve(num)
