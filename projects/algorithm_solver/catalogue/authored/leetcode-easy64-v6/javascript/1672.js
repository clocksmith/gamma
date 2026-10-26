'use strict';

// 1672. Richest Customer Wealth (Easy).
// Specification: https://leetcode.com/problems/richest-customer-wealth/description/
// O(m * n) time, O(1) space; preserve accounts and its rows.
function solve(accounts) {
  let maximum = 0;
  for (const balances of accounts) {
    let wealth = 0;
    for (const balance of balances) wealth += balance;
    maximum = Math.max(maximum, wealth);
  }
  return maximum;
}

const maximumWealth = solve;
class Solution {
  maximumWealth(accounts) { return solve(accounts); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumWealth };
