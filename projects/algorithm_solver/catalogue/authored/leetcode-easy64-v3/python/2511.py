"""2511. Maximum Enemy Forts That Can Be Captured (Easy).

Specification: https://leetcode.com/problems/maximum-enemy-forts-that-can-be-captured/description/
"""


def solve(forts: list[int]) -> int:
    """O(n) time, O(1) space; inspect gaps between opposite nonzero endpoints."""
    previous = -1
    largest = 0
    for index, value in enumerate(forts):
        if value == 0:
            continue
        if previous != -1 and value != forts[previous]:
            largest = max(largest, index - previous - 1)
        previous = index
    return largest


class Solution:
    def captureForts(self, forts: list[int]) -> int:
        return solve(forts)
