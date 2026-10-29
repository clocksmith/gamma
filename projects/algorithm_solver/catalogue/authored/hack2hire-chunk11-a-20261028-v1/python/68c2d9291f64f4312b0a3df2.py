"""Hack2Hire 68c2d9291f64f4312b0a3df2 (Find Median In Large Array) over an INFERRED spec; qualification unknown."""


def solve(nums):
    state = [20261029]

    def draw(m):  # Park-Miller generator; products stay below 2**47 so JavaScript matches exactly
        state[0] = state[0] * 48271 % 2147483647
        return state[0] % m

    def select(values, k):  # quickselect with three-way partitioning on fresh lists
        while True:
            pivot = values[draw(len(values))]
            lows = [x for x in values if x < pivot]
            if k < len(lows):
                values = lows
                continue
            highs = [x for x in values if x > pivot]
            below_highs = len(values) - len(highs)
            if k >= below_highs:
                values, k = highs, k - below_highs
                continue
            return pivot

    n = len(nums)
    if n % 2:
        return select(nums, n // 2)
    total = select(nums, n // 2 - 1) + select(nums, n // 2)
    return total // 2 if total % 2 == 0 else total / 2


class Solution:
    def findMedian(self, nums):
        return solve(nums)
