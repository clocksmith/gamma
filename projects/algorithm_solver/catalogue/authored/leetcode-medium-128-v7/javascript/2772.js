'use strict';

// 2772. Apply Operations to Make All Array Elements Equal to Zero: start exactly the decrements needed at each index and expire them after k positions.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums, k) {
  const changes = new Array(nums.length + 1).fill(0);
  let active = 0;
  for (let index = 0; index < nums.length; index += 1) {
    active += changes[index];
    const needed = nums[index] - active;
    if (needed < 0) return false;
    if (needed > 0) {
      if (index + k > nums.length) return false;
      active += needed;
      changes[index + k] -= needed;
    }
  }
  return true;
}

const checkArray = solve;
class Solution {
  checkArray(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkArray };
