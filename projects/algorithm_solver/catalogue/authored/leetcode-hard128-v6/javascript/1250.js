'use strict';

// 1250. Check If It Is a Good Array.
// Bezout identity reduces the question to the array gcd; O(n log M) time, O(1) auxiliary space. Inputs are preserved.

function solve(nums) {
  let common = 0;
  for (const value of nums) {
    let a = common, b = value;
    while (b !== 0) [a, b] = [b, a % b];
    common = a;
    if (common === 1) return true;
  }
  return false;
}

const isGoodArray = solve;
class Solution {
  isGoodArray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isGoodArray };
