'use strict';

// 728. Self Dividing Numbers (Easy).
// Specification: https://leetcode.com/problems/self-dividing-numbers/description/
// O((right - left + 1) * d) time, O(1) auxiliary space excluding output; reject zero digits.
function solve(left, right) {
  const result = [];
  for (let value = left; value <= right; value++) {
    let remaining = value;
    let valid = true;
    while (remaining > 0) {
      const digit = remaining % 10;
      if (digit === 0 || value % digit !== 0) {
        valid = false;
        break;
      }
      remaining = Math.floor(remaining / 10);
    }
    if (valid) result.push(value);
  }
  return result;
}

const selfDividingNumbers = solve;
class Solution {
  selfDividingNumbers(left, right) { return solve(left, right); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, selfDividingNumbers };
