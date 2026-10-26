'use strict';

// 2811. Check if it is Possible to Split Array: use an adjacent qualifying pair as the final nonsingleton piece.
// O(n) time and O(1) auxiliary space for positive inputs; inputs are read-only.
function solve(nums, m) {
  if (nums.length <= 2) return true;
  for (let index = 1; index < nums.length; index += 1) {
    if (nums[index - 1] + nums[index] >= m) return true;
  }
  return false;
}

const canSplitArray = solve;
class Solution {
  canSplitArray(nums, m) { return solve(nums, m); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canSplitArray };
