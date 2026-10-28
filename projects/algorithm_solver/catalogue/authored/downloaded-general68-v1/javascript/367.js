'use strict';

// 367. Valid Perfect Square (Easy).
// Specification: https://leetcode.com/problems/valid-perfect-square/description/
function solve(num) {
  let left = 1; let right = num;
  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    const square = mid * mid;
    if (square === num) return true;
    if (square < num) left = mid + 1;
    else right = mid - 1;
  }
  return false;
}
const isPerfectSquare = solve;
class Solution { isPerfectSquare(num) { return solve(num); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isPerfectSquare };
