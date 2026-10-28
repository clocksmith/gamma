"""1238. Circular Permutation in Binary Representation (Medium).

Specification: https://leetcode.com/problems/circular-permutation-in-binary-representation/description/
"""


def solve(n: int, start: int) -> list[int]:
    total = 1 << n
    gray = [i ^ (i >> 1) for i in range(total)]
    index = gray.index(start)
    return gray[index:] + gray[:index]


class Solution:
    def circularPermutation(self, n: int, start: int) -> list[int]:
        return solve(n, start)
