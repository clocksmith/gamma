'use strict';

// 2520. Count the Digits That Divide a Number (Easy).
// Specification: https://leetcode.com/problems/count-the-digits-that-divide-a-number/description/
// O(log num) time, O(1) space. Count repeated digits separately.
function solve(num) {
  let remaining = num;
  let count = 0;
  while (remaining > 0) {
    const digit = remaining % 10;
    if (digit !== 0 && num % digit === 0) count++;
    remaining = Math.floor(remaining / 10);
  }
  return count;
}

const countDigits = solve;
class Solution {
  countDigits(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countDigits };
