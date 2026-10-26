'use strict';

// 3875. Construct Uniform Parity Array I (Easy).
// Specification: https://leetcode.com/problems/construct-uniform-parity-array-i/description/
// O(1) time and space; existence follows from parity; preserve nums1.
function solve(nums1) {
  // If all values are even, keep them. Otherwise keep every odd value and
  // subtract one original odd value from each even value, making all values odd.
  // The chosen odd index differs from every even index, as required.
  return true;
}

const uniformArray = solve;
class Solution {
  uniformArray(nums1) { return solve(nums1); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, uniformArray };
