class Solution:
    def maxProfit(self, prices: list[int]) -> int:
        if not prices:
            return 0

        first_cost = prices[0]
        first_profit = 0
        second_cost = prices[0]
        second_profit = 0
        for price in prices:
            first_cost = min(first_cost, price)
            first_profit = max(first_profit, price - first_cost)
            second_cost = min(second_cost, price - first_profit)
            second_profit = max(second_profit, price - second_cost)
        return second_profit
