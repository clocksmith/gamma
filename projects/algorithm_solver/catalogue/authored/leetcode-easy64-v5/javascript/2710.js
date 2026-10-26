'use strict';

// 2710. Remove Trailing Zeros From a String (Easy).
// Specification: https://leetcode.com/problems/remove-trailing-zeros-from-a-string/description/
// O(n) time, O(n) result space; do not convert the decimal string to a number.
function solve(num) {
  let end = num.length;
  while (end > 1 && num[end - 1] === '0') end--;
  return num.slice(0, end);
}

const removeTrailingZeros = solve;
class Solution {
  removeTrailingZeros(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeTrailingZeros };
