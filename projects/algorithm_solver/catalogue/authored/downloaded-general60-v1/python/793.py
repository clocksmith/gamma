"""793. Preimage Size of Factorial Zeroes Function (Hard).

Specification: https://leetcode.com/problems/preimage-size-of-factorial-zeroes-function/description/
"""


def _trailing_zeroes(n):
    count = 0
    while n > 0:
        n //= 5
        count += n
    return count


def solve(k: int) -> int:
    left, right = 0, 5000000000
    while left < right:
        mid = (left + right) // 2
        if _trailing_zeroes(mid) < k:
            left = mid + 1
        else:
            right = mid
    return 5 if _trailing_zeroes(left) == k else 0


class Solution:
    def preimageSizeFZF(self, k: int) -> int:
        return solve(k)
