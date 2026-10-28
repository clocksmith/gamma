"""779. K-th Symbol in Grammar (Medium).

Specification: https://leetcode.com/problems/k-th-symbol-in-grammar/description/
"""


def solve(n: int, k: int) -> int:
    value = k - 1
    parity = 0
    while value > 0:
        parity ^= value & 1
        value >>= 1
    return parity


class Solution:
    def kthGrammar(self, n: int, k: int) -> int:
        return solve(n, k)
