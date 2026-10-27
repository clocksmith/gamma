"""4069. Best Time to Buy and Sell Stock with Cooldown II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-cooldown-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4069.Best%20Time%20to%20Buy%20and%20Sell%20Stock%20with%20Cooldown%20II/README_EN.md
Complexity: O(n^2) time, O(n) space.
Arbitrary duration-dependent fee is charged once per completed transaction. A buy at i can follow a prior sale only through day i-cooldown-1. Zero transactions remain available. Inputs preserved.
"""

from __future__ import annotations

def solve(prices, cooldown, costs):
    n = len(prices)
    best = [0]*(n+1)
    for sell in range(n):
        value = best[sell]
        for buy in range(sell):
            earlier = best[max(0, buy-cooldown)]
            value = max(value, earlier+prices[sell]-prices[buy]-costs[sell-buy])
        best[sell+1] = value
    return best[n]
