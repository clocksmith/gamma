'use strict';

// 1798. Maximum Number of Consecutive Values You Can Make (Medium).
// Specification: https://leetcode.com/problems/maximum-number-of-consecutive-values-you-can-make/description/
function solve(coins) {
  const sorted = coins.slice().sort((a, b) => a - b);
  let reachable = 0;
  for (const coin of sorted) {
    if (coin > reachable + 1) break;
    reachable += coin;
  }
  return reachable + 1;
}
const getMaximumConsecutive = solve;
class Solution { getMaximumConsecutive(coins) { return solve(coins); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, getMaximumConsecutive };
