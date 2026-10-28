'use strict';

// 2898. Maximum Linear Stock Score (Medium).
// Specification: https://leetcode.com/problems/maximum-linear-stock-score/description/
function solve(prices) {
  const sums = new Map();
  for (let i = 0; i < prices.length; i++) {
    const key = prices[i] - (i + 1);
    sums.set(key, (sums.get(key) || 0) + prices[i]);
  }
  let ans = 0;
  for (const v of sums.values()) ans = Math.max(ans, v);
  return ans;
}
const maximumScore = solve;
class Solution {
  maximumScore(...args) { return solve(...args); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumScore };
