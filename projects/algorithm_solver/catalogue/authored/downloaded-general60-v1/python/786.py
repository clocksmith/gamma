"""786. K-th Smallest Prime Fraction (Medium).

Specification: https://leetcode.com/problems/k-th-smallest-prime-fraction/description/
"""


def solve(arr: list[int], k: int) -> list[int]:
    fractions = []
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            fractions.append((arr[i] / arr[j], arr[i], arr[j]))
    fractions.sort(key=lambda item: item[0])
    return [fractions[k - 1][1], fractions[k - 1][2]]


class Solution:
    def kthSmallestPrimeFraction(self, arr: list[int], k: int) -> list[int]:
        return solve(arr, k)
