"""69. Sqrt(x) (Easy).

Specification: https://leetcode.com/problems/sqrtx/description/
"""


def solve(x: int) -> int:
    """O(log x) time, O(1) space; compare using integer division rather than squaring."""
    left, right = 0, x
    answer = 0
    while left <= right:
        middle = left + (right - left) // 2
        if middle == 0 or middle <= x // middle:
            answer = middle
            left = middle + 1
        else:
            right = middle - 1
    return answer


class Solution:
    def mySqrt(self, x: int) -> int:
        return solve(x)
