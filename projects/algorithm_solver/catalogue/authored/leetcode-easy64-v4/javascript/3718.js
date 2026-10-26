'use strict';

// 3718. Smallest Missing Multiple of K (Easy).
// Specification: https://leetcode.com/problems/smallest-missing-multiple-of-k/description/
// O(n) expected time and space; at most n present multiples can be skipped.
function solve(nums, k) {
  const present = new Set(nums);
  let candidate = k;
  while (present.has(candidate)) candidate += k;
  return candidate;
}

const missingMultiple = solve;
class Solution {
  missingMultiple(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, missingMultiple };
