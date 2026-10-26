'use strict';

// 3370. Smallest Number With All Set Bits (Easy).
// Specification: https://leetcode.com/problems/smallest-number-with-all-set-bits/description/
// O(log n) time, O(1) space; grow numbers of the form 2^bits - 1.
function solve(n) {
  let result = 1;
  while (result < n) result = result * 2 + 1;
  return result;
}

const smallestNumber = solve;
class Solution {
  smallestNumber(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestNumber };
