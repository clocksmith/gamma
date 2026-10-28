'use strict';

// 1599. Maximum Profit of Operating a Centennial Wheel (Medium).
// Specification: https://leetcode.com/problems/maximum-profit-of-operating-a-centennial-wheel/description/
function solve(customers, boardingCost, runningCost) {
  let waiting = 0; let profit = 0; let bestProfit = 0; let bestRotation = -1;
  let rotation = 0;
  while (waiting > 0 || rotation < customers.length) {
    if (rotation < customers.length) waiting += customers[rotation];
    const boarded = Math.min(4, waiting);
    waiting -= boarded;
    profit += boarded * boardingCost - runningCost;
    rotation++;
    if (profit > bestProfit) { bestProfit = profit; bestRotation = rotation; }
  }
  return bestRotation;
}
const minOperationsMaxProfit = solve;
class Solution { minOperationsMaxProfit(customers, boardingCost, runningCost) { return solve(customers, boardingCost, runningCost); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperationsMaxProfit };
