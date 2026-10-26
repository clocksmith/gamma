'use strict';

// 2770. Maximum Number of Jumps to Reach the Last Index: compute the longest reachable path through increasing array indices.
// O(n * n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums, target) {
  const jumps = new Int32Array(nums.length).fill(-1);
  jumps[0] = 0;
  for (let right = 1; right < nums.length; right += 1) {
    for (let left = 0; left < right; left += 1) {
      if (jumps[left] !== -1 && Math.abs(nums[right] - nums[left]) <= target) {
        jumps[right] = Math.max(jumps[right], jumps[left] + 1);
      }
    }
  }
  return jumps[nums.length - 1];
}

const maximumJumps = solve;
class Solution {
  maximumJumps(nums, target) { return solve(nums, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumJumps };
