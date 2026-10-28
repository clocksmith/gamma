class Solution:
    def maxProfit(self, k, prices):
        if k >= len(prices) // 2:
            return sum(max(0, following - previous) for previous, following in zip(prices, prices[1:]))
        cash = [0] * (k + 1)
        hold = [float('-inf')] * (k + 1)
        for price in prices:
            next_cash, next_hold = cash[:], hold[:]
            for count in range(1, k + 1):
                next_hold[count] = max(hold[count], cash[count - 1] - price)
                next_cash[count] = max(cash[count], hold[count] + price)
            cash, hold = next_cash, next_hold
        return cash[k]
