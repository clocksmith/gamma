'use strict';

// 3876. Construct Uniform Parity Array II.
// O(n) time and O(1) space; the minimum cannot change parity, and an odd minimum can convert every larger even value.
function solve(nums1) {
  let smallest = Infinity;
  let allEven = true;
  for (const value of nums1) {
    smallest = Math.min(smallest, value);
    if (value % 2 !== 0) allEven = false;
  }
  return smallest % 2 === 1 || allEven;
}

const uniformArray = solve;
class Solution {
  uniformArray(nums1) { return solve(nums1); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, uniformArray };
