'use strict';

// 69. Sqrt(x) (Easy).
// Specification: https://leetcode.com/problems/sqrtx/description/
// O(log x) time, O(1) space; compare using integer division rather than squaring.
function solve(x) {
  let left = 0;
  let right = x;
  let answer = 0;
  while (left <= right) {
    const middle = left + Math.floor((right - left) / 2);
    if (middle === 0 || middle <= Math.floor(x / middle)) {
      answer = middle;
      left = middle + 1;
    } else {
      right = middle - 1;
    }
  }
  return answer;
}

const mySqrt = solve;
class Solution {
  mySqrt(x) { return solve(x); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mySqrt };
