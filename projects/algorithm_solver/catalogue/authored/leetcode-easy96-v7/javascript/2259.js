'use strict';

// 2259. Remove Digit From Number to Maximize Result (Easy).
// Specification: https://leetcode.com/problems/remove-digit-from-number-to-maximize-result/description/
// O(n) time and output space; remove before the first increase, otherwise remove the last occurrence.
function solve(number, digit) {
  let last = -1;
  for (let index = 0; index < number.length; index++) {
    if (number[index] !== digit) continue;
    last = index;
    if (index + 1 < number.length && number[index + 1] > digit) {
      return number.slice(0, index) + number.slice(index + 1);
    }
  }
  return number.slice(0, last) + number.slice(last + 1);
}

const removeDigit = solve;
class Solution {
  removeDigit(number, digit) { return solve(number, digit); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeDigit };
