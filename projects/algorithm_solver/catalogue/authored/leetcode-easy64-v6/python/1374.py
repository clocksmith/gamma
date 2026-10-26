"""1374. Generate a String With Characters That Have Odd Counts (Easy).

Specification: https://leetcode.com/problems/generate-a-string-with-characters-that-have-odd-counts/description/
"""


def solve(n: int) -> str:
    """O(n) time and result space; use one odd run or two odd runs."""
    return 'a' * n if n % 2 == 1 else 'a' * (n - 1) + 'b'


class Solution:
    def generateTheString(self, n: int) -> str:
        return solve(n)
