"""3226. Number of Bit Changes to Make Two Integers Equal (Easy).

Specification: https://leetcode.com/problems/number-of-bit-changes-to-make-two-integers-equal/description/
"""


def solve(n: int, k: int) -> int:
    """O(log(n + k)) time, O(1) space; bitwise operations are safe for n, k <= 1000000."""
    if n & k != k:
        return -1
    remaining = n ^ k
    changes = 0
    while remaining:
        remaining &= remaining - 1
        changes += 1
    return changes


class Solution:
    def minChanges(self, n: int, k: int) -> int:
        return solve(n, k)
