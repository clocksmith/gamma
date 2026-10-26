'use strict';

// 3146. Permutation Difference between Two Strings (Easy).
// Specification: https://leetcode.com/problems/permutation-difference-between-two-strings/description/
// O(n) time, O(1) alphabet space; strings are permutations of distinct lowercase letters.
function solve(s, t) {
  const positions = new Array(26).fill(0);
  for (let index = 0; index < s.length; index++) positions[s.charCodeAt(index) - 97] = index;
  let difference = 0;
  for (let index = 0; index < t.length; index++) {
    difference += Math.abs(index - positions[t.charCodeAt(index) - 97]);
  }
  return difference;
}

const findPermutationDifference = solve;
class Solution {
  findPermutationDifference(s, t) { return solve(s, t); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findPermutationDifference };
