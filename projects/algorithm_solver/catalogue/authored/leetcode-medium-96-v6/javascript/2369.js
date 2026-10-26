'use strict';

// 2369. Check if There is a Valid Partition For The Array: extend valid prefixes by equal pairs or one of the two permitted triples.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const valid = new Array(nums.length + 1).fill(false);
  valid[0] = true;
  for (let end = 2; end <= nums.length; end += 1) {
    if (nums[end - 1] === nums[end - 2] && valid[end - 2]) valid[end] = true;
    if (end >= 3 && valid[end - 3]) {
      const equal = nums[end - 3] === nums[end - 2] && nums[end - 2] === nums[end - 1];
      const consecutive = nums[end - 3] + 1 === nums[end - 2] && nums[end - 2] + 1 === nums[end - 1];
      if (equal || consecutive) valid[end] = true;
    }
  }
  return valid[nums.length];
}

const validPartition = solve;
class Solution {
  validPartition(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, validPartition };
