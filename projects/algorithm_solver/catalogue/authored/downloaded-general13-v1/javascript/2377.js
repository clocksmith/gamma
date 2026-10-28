'use strict';

// 2377. Check if Number Has Equal Digit Count and Digit Value (Easy).
// Specification: https://leetcode.com/problems/check-if-number-has-equal-digit-count-and-digit-value/description/
function solve(num) {
  for (let i = 0; i < num.length; i++) {
    let count = 0;
    for (const ch of num) if (ch === String(i)) count++;
    if (count !== Number(num[i])) return false;
  }
  return true;
}
const digitCount = solve;
class Solution { digitCount(num) { return solve(num); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, digitCount };
