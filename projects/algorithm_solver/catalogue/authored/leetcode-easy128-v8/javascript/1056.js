'use strict';

// 1056. Confusing Number (Easy).
// Specification: https://leetcode.com/problems/confusing-number/description/
// O(d) time, O(1) space; rotate valid digits in reverse order and require a changed value.
function solve(n) {
  const rotatedDigit = [0, 1, -1, -1, -1, -1, 9, -1, 8, 6];
  let remaining = n;
  let rotated = 0;
  while (remaining > 0) {
    const digit = remaining % 10;
    if (rotatedDigit[digit] < 0) return false;
    rotated = rotated * 10 + rotatedDigit[digit];
    remaining = Math.floor(remaining / 10);
  }
  return rotated !== n;
}

const confusingNumber = solve;
class Solution {
  confusingNumber(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, confusingNumber };
