'use strict';

// 2544. Alternating Digit Sum (Easy).
// Specification: https://leetcode.com/problems/alternating-digit-sum/description/
// O(d) time and digit-string space; alternate signs starting positive at the most significant digit.
function solve(n) {
  let result = 0;
  let sign = 1;
  for (const character of String(n)) {
    result += sign * (character.charCodeAt(0) - 48);
    sign = -sign;
  }
  return result;
}

const alternateDigitSum = solve;
class Solution {
  alternateDigitSum(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, alternateDigitSum };
