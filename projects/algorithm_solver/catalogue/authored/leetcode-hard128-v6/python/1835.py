"""1835. Find XOR Sum of All Pairs Bitwise AND.

Distribute bitwise AND over XOR; O(n+m) time, O(1) space. Inputs are preserved.
"""

def solve(arr1: list[int], arr2: list[int]) -> int:
    first = second = 0
    for value in arr1:
        first ^= value
    for value in arr2:
        second ^= value
    return first & second


class Solution:
    def getXORSum(self, arr1: list[int], arr2: list[int]) -> int:
        return solve(arr1, arr2)
