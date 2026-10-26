'use strict';

// 2202. Maximize the Topmost Element After K Moves: compare recoverable removed elements with the untouched kth element.
// O(min(n, k) + 1) time and O(1) auxiliary space; inputs are read-only.
function solve(nums, k) {
  if (k === 0) return nums[0];
  if (nums.length === 1) return k % 2 === 0 ? nums[0] : -1;
  let best = -1;
  for (let index = 0; index < Math.min(nums.length, k - 1); index += 1) {
    best = Math.max(best, nums[index]);
  }
  if (k < nums.length) best = Math.max(best, nums[k]);
  return best;
}

const maximumTop = solve;
class Solution {
  maximumTop(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumTop };
