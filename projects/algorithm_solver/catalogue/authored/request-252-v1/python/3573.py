# Original candidate; contract and evidence: ../batch1/manifest.json
def solve(prices, k):
    cash = [float('-inf')] * (k + 1)
    long = cash.copy()
    short = cash.copy()
    cash[0] = 0
    for price in prices:
        next_cash, next_long, next_short = cash.copy(), long.copy(), short.copy()
        for done in range(k):
            next_long[done] = max(long[done], cash[done] - price)
            next_short[done] = max(short[done], cash[done] + price)
            next_cash[done + 1] = max(cash[done + 1], long[done] + price, short[done] - price)
        cash, long, short = next_cash, next_long, next_short
    return max(cash)
