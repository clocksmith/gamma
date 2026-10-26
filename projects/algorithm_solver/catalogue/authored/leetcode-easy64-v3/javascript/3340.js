'use strict';

// 3340. Check Balanced String (Easy).
// Specification: https://leetcode.com/problems/check-balanced-string/description/
// O(n) time, O(1) space; compare alternating sums of decimal digits.
function solve(num) {
  let difference = 0;
  for (let index = 0; index < num.length; index++) {
    const digit = num.charCodeAt(index) - 48;
    difference += index % 2 === 0 ? digit : -digit;
  }
  return difference === 0;
}

const isBalanced = solve;
class Solution {
  isBalanced(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isBalanced };
