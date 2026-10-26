'use strict';

// 1835. Find XOR Sum of All Pairs Bitwise AND.
// Distribute bitwise AND over XOR; O(n+m) time, O(1) space. Inputs are preserved.

function solve(arr1, arr2) {
  let first = 0, second = 0;
  for (const value of arr1) first ^= value;
  for (const value of arr2) second ^= value;
  return first & second;
}

const getXORSum = solve;
class Solution {
  getXORSum(arr1, arr2) { return solve(arr1, arr2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getXORSum };
