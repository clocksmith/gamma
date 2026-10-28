"""829. Consecutive Numbers Sum (Hard).

Specification: https://leetcode.com/problems/consecutive-numbers-sum/description/
"""


def solve(n: int) -> int:
    count = 0
    k = 1
    while k * (k - 1) // 2 < n:
        if (n - k * (k - 1) // 2) % k == 0:
            count += 1
        k += 1
    return count


class Solution:
    def consecutiveNumbersSum(self, n: int) -> int:
        return solve(n)
