"""1475. Final Prices With a Special Discount in a Shop (Easy).

Specification: https://leetcode.com/problems/final-prices-with-a-special-discount-in-a-shop/description/
"""


def solve(prices: list[int]) -> list[int]:
    result = prices[:]
    stack = []
    for i, value in enumerate(prices):
        while stack and prices[stack[-1]] >= value:
            index = stack.pop()
            result[index] -= value
        stack.append(i)
    return result


class Solution:
    def finalPrices(self, prices: list[int]) -> list[int]:
        return solve(prices)
