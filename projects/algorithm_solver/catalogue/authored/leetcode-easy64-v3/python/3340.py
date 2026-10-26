"""3340. Check Balanced String (Easy).

Specification: https://leetcode.com/problems/check-balanced-string/description/
"""


def solve(num: str) -> bool:
    """O(n) time, O(1) space; compare alternating sums of decimal digits."""
    difference = 0
    for index, character in enumerate(num):
        digit = ord(character) - ord('0')
        difference += digit if index % 2 == 0 else -digit
    return difference == 0


class Solution:
    def isBalanced(self, num: str) -> bool:
        return solve(num)
