'use strict';

// 1011. Capacity To Ship Packages Within D Days (Medium).
// Specification: https://leetcode.com/problems/capacity-to-ship-packages-within-d-days/description/
function daysNeeded(weights, capacity) {
  let days = 1; let load = 0;
  for (const value of weights) {
    if (load + value > capacity) { days++; load = value; }
    else load += value;
  }
  return days;
}
function solve(weights, days) {
  let left = Math.max(...weights); let right = weights.reduce((sum, value) => sum + value, 0);
  while (left < right) {
    const mid = Math.floor((left + right) / 2);
    if (daysNeeded(weights, mid) <= days) right = mid;
    else left = mid + 1;
  }
  return left;
}
const shipWithinDays = solve;
class Solution { shipWithinDays(weights, days) { return solve(weights, days); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, shipWithinDays };
