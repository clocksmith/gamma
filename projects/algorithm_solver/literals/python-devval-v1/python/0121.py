def solve(prices):
    minimum = prices[0]
    profit = 0
    for price in prices:
        profit = max(profit, price - minimum)
        minimum = min(minimum, price)
    return profit
