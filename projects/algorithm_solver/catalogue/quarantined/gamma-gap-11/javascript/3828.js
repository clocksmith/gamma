'use strict';

// 3828. Final Element After Subarray Deletions.
// O(1) time and space; Alice can retain either endpoint, and Bob can retain an original endpoint after any nonfinal move.
function solve(nums) {
  return Math.max(nums[0], nums[nums.length - 1]);
}

const finalElement = solve;
class Solution {
  finalElement(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, finalElement };
