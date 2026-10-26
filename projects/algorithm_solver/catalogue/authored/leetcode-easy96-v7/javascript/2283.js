'use strict';

// 2283. Check if Number Has Equal Digit Count and Digit Value (Easy).
// Specification: https://leetcode.com/problems/check-if-number-has-equal-digit-count-and-digit-value/description/
// O(n) time, O(1) space for decimal digits; compare positions to digit frequencies.
function solve(num) {
  const counts = new Array(10).fill(0);
  for (const character of num) counts[character.charCodeAt(0) - 48]++;
  for (let index = 0; index < num.length; index++) {
    if (counts[index] !== num.charCodeAt(index) - 48) return false;
  }
  return true;
}

const digitCount = solve;
class Solution {
  digitCount(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, digitCount };
