/**
 * 4069. Best Time to Buy and Sell Stock with Cooldown II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-cooldown-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4069.Best%20Time%20to%20Buy%20and%20Sell%20Stock%20with%20Cooldown%20II/README_EN.md
 * Complexity: O(n^2) time, O(n) space.
 * Arbitrary duration-dependent fee is charged once per completed transaction. A buy at i can follow a prior sale only through day i-cooldown-1. Zero transactions remain available. Inputs preserved.
 */

function solve(prices,cooldown,costs) {
  const n=prices.length,best=new Float64Array(n+1);
  for(let sell=0;sell<n;sell++) {
    let value=best[sell];
    for(let buy=0;buy<sell;buy++)value=Math.max(value,best[Math.max(0,buy-cooldown)]+prices[sell]-prices[buy]-costs[sell-buy]);
    best[sell+1]=value;
  }
  return best[n];
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
