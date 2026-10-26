"""1534. Count Good Triplets (Easy).

Specification: https://leetcode.com/problems/count-good-triplets/description/
"""


def solve(arr: list[int], a: int, b: int, c: int) -> int:
    """O(n^3) time, O(1) auxiliary space; count ordered index triples meeting all three bounds."""
    total = 0
    for first in range(len(arr) - 2):
        for second in range(first + 1, len(arr) - 1):
            if abs(arr[first] - arr[second]) > a:
                continue
            for third in range(second + 1, len(arr)):
                if abs(arr[second] - arr[third]) <= b and abs(arr[first] - arr[third]) <= c:
                    total += 1
    return total


class Solution:
    def countGoodTriplets(self, arr: list[int], a: int, b: int, c: int) -> int:
        return solve(arr, a, b, c)
