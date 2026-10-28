"""1052. Grumpy Bookstore Owner (Medium).

Specification: https://leetcode.com/problems/grumpy-bookstore-owner/description/
"""


def solve(customers: list[int], grumpy: list[int], minutes: int) -> int:
    base = 0
    for i, value in enumerate(customers):
        if grumpy[i] == 0:
            base += value
    extra = 0
    window = 0
    for i, value in enumerate(customers):
        if grumpy[i] == 1:
            window += value
        if i >= minutes and grumpy[i - minutes] == 1:
            window -= customers[i - minutes]
        extra = max(extra, window)
    return base + extra


class Solution:
    def maxSatisfied(self, customers: list[int], grumpy: list[int], minutes: int) -> int:
        return solve(customers, grumpy, minutes)
