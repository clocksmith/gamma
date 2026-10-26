'use strict';

// 2264. Largest 3-Same-Digit Number in String (Easy).
// Specification: https://leetcode.com/problems/largest-3-same-digit-number-in-string/description/
// O(n) time, O(1) auxiliary space; retain leading zeros in the returned string.
function solve(num) {
  let result = '';
  for (let index = 2; index < num.length; index++) {
    if (num[index] === num[index - 1] && num[index] === num[index - 2]) {
      const candidate = num.slice(index - 2, index + 1);
      if (candidate > result) result = candidate;
    }
  }
  return result;
}

const largestGoodInteger = solve;
class Solution {
  largestGoodInteger(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestGoodInteger };
