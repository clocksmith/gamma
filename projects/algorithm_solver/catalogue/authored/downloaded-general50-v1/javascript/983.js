'use strict';

// 983. Minimum Cost For Tickets (Medium).
// Specification: https://leetcode.com/problems/minimum-cost-for-tickets/description/
function solve(days, costs) {
  const daySet = new Set(days);
  const last = days[days.length - 1];
  const dp = new Array(last + 1).fill(0);
  for (let day = 1; day <= last; day++) {
    if (!daySet.has(day)) dp[day] = dp[day - 1];
    else dp[day] = Math.min(dp[day - 1] + costs[0], dp[Math.max(0, day - 7)] + costs[1], dp[Math.max(0, day - 30)] + costs[2]);
  }
  return dp[last];
}
const mincostTickets = solve;
class Solution { mincostTickets(days, costs) { return solve(days, costs); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, mincostTickets };
