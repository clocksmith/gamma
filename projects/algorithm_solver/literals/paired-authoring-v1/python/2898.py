class Solution:
    def maxScore(self, prices):
        totals = {}
        best = 0
        for index, price in enumerate(prices):
            diagonal = price - index
            totals[diagonal] = totals.get(diagonal, 0) + price
            best = max(best, totals[diagonal])
        return best
