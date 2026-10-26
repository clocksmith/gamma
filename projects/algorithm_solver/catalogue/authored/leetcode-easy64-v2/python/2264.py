"""2264. Largest 3-Same-Digit Number in String (Easy).

Specification: https://leetcode.com/problems/largest-3-same-digit-number-in-string/description/
"""


def solve(num: str) -> str:
    """O(n) time, O(1) auxiliary space; retain leading zeros in the returned string."""
    result = ''
    for index in range(2, len(num)):
        if num[index] == num[index - 1] == num[index - 2]:
            candidate = num[index - 2:index + 1]
            if candidate > result:
                result = candidate
    return result


class Solution:
    def largestGoodInteger(self, num: str) -> str:
        return solve(num)
