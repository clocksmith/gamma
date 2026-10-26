'use strict';

// 2560. House Robber IV: binary search the smallest capability allowing a greedy nonadjacent selection.
// O(n log(M + 1)) time and O(1) auxiliary space, where M is the largest value; inputs are read-only.
function solve(nums, k) {
  let low = nums[0];
  let high = nums[0];
  for (const value of nums) {
    low = Math.min(low, value);
    high = Math.max(high, value);
  }
  while (low < high) {
    const capability = Math.floor((low + high) / 2);
    let count = 0;
    let index = 0;
    while (index < nums.length) {
      if (nums[index] <= capability) {
        count += 1;
        index += 2;
      } else index += 1;
    }
    if (count >= k) high = capability;
    else low = capability + 1;
  }
  return low;
}

const minCapability = solve;
class Solution {
  minCapability(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCapability };
