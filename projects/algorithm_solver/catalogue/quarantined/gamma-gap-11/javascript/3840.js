'use strict';

// 3840. House Robber V.
// O(n) time and O(1) space; only equal-color adjacent selections conflict.
function solve(nums, colors) {
  let skipped = 0;
  let taken = 0;
  for (let index = 0; index < nums.length; index += 1) {
    const best = Math.max(skipped, taken);
    const nextTaken = (index > 0 && colors[index] === colors[index - 1] ? skipped : best) + nums[index];
    skipped = best;
    taken = nextTaken;
  }
  return Math.max(skipped, taken);
}

const rob = solve;
class Solution {
  rob(nums, colors) { return solve(nums, colors); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, rob };
