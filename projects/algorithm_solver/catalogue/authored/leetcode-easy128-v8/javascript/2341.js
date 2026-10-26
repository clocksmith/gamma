'use strict';

// 2341. Maximum Number of Pairs in Array (Easy).
// Specification: https://leetcode.com/problems/maximum-number-of-pairs-in-array/description/
// O(n) expected time, O(u) space; match each new value against an unmatched equal value.
function solve(nums) {
  const unmatched = new Set();
  let pairs = 0;
  for (const value of nums) {
    if (unmatched.has(value)) {
      unmatched.delete(value);
      pairs++;
    } else {
      unmatched.add(value);
    }
  }
  return [pairs, unmatched.size];
}

const numberOfPairs = solve;
class Solution {
  numberOfPairs(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfPairs };
