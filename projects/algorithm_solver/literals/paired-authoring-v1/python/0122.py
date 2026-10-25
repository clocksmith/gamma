class Solution:
    def maxProfit(self, prices: list[int]) -> int:
        profit = 0
        for index in range(1, len(prices)):
            increase = prices[index] - prices[index - 1]
            if increase > 0:
                profit += increase
        return profit
