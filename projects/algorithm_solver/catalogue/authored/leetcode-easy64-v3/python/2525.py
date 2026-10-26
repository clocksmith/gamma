"""2525. Categorize Box According to Criteria (Easy).

Specification: https://leetcode.com/problems/categorize-box-according-to-criteria/description/
"""


def solve(length: int, width: int, height: int, mass: int) -> str:
    """O(1) time and space; integer volume is at most 10^15, exact in Number."""
    bulky = (length >= 10000 or width >= 10000 or height >= 10000
             or length * width * height >= 1000000000)
    heavy = mass >= 100
    if bulky and heavy:
        return 'Both'
    if bulky:
        return 'Bulky'
    if heavy:
        return 'Heavy'
    return 'Neither'


class Solution:
    def categorizeBox(self, length: int, width: int, height: int, mass: int) -> str:
        return solve(length, width, height, mass)
