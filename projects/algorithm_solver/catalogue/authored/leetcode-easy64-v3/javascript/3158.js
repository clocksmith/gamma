'use strict';

// 3158. Find the XOR of Numbers Which Appear Twice (Easy).
// Specification: https://leetcode.com/problems/find-the-xor-of-numbers-which-appear-twice/description/
// O(n) expected time, O(n) space; every value occurs at most twice and fits int32.
function solve(nums) {
  const seen = new Set();
  let result = 0;
  for (const value of nums) {
    if (seen.has(value)) result ^= value;
    else seen.add(value);
  }
  return result;
}

const duplicateNumbersXOR = solve;
class Solution {
  duplicateNumbersXOR(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, duplicateNumbersXOR };
