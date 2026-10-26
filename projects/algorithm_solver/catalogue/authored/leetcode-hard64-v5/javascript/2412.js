'use strict';

// 2412. Minimum Money Required Before Transactions. Combine all possible losses with the largest final transaction requirement; O(n) time and O(1) space. Inputs are preserved.

function solve(transactions) {
  let losses = 0;
  let reserve = 0;
  for (const [cost, cashback] of transactions) {
    losses += Math.max(0, cost - cashback);
    reserve = Math.max(reserve, Math.min(cost, cashback));
  }
  return losses + reserve;
}

const minimumMoney = solve;
class Solution {
  minimumMoney(transactions) { return solve(transactions); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumMoney };
