'use strict';

// 2806. Account Balance After Rounded Purchase (Easy).
// Specification: https://leetcode.com/problems/account-balance-after-rounded-purchase/description/
// O(1) time and space; half-way values round upward, not to an even multiple.
function solve(purchaseAmount) {
  const rounded = 10 * Math.floor((purchaseAmount + 5) / 10);
  return 100 - rounded;
}

const accountBalanceAfterPurchase = solve;
class Solution {
  accountBalanceAfterPurchase(purchaseAmount) { return solve(purchaseAmount); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, accountBalanceAfterPurchase };
