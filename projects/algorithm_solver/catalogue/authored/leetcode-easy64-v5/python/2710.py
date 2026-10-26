"""2710. Remove Trailing Zeros From a String (Easy).

Specification: https://leetcode.com/problems/remove-trailing-zeros-from-a-string/description/
"""


def solve(num: str) -> str:
    """O(n) time, O(n) result space; do not convert the decimal string to a number."""
    end = len(num)
    while end > 1 and num[end - 1] == '0':
        end -= 1
    return num[:end]


class Solution:
    def removeTrailingZeros(self, num: str) -> str:
        return solve(num)
