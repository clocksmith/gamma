'use strict';

// 829. Consecutive Numbers Sum (Hard).
// Specification: https://leetcode.com/problems/consecutive-numbers-sum/description/
function solve(n) {
  let count = 0;
  for (let k = 1; k * (k - 1) / 2 < n; k++) {
    if ((n - k * (k - 1) / 2) % k === 0) count++;
  }
  return count;
}
const consecutiveNumbersSum = solve;
class Solution { consecutiveNumbersSum(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, consecutiveNumbersSum };
