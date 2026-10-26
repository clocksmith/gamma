'use strict';

// 2420. Find All Good Indices: check monotone runs immediately before and after each excluded center.
// O(n) time and O(n) auxiliary and result space; inputs are read-only.
function solve(nums, k) {
  const size = nums.length;
  const before = new Int32Array(size).fill(1);
  const after = new Int32Array(size).fill(1);
  for (let index = 1; index < size; index += 1) {
    if (nums[index] <= nums[index - 1]) before[index] = before[index - 1] + 1;
  }
  for (let index = size - 2; index >= 0; index -= 1) {
    if (nums[index] <= nums[index + 1]) after[index] = after[index + 1] + 1;
  }
  const result = [];
  for (let index = k; index < size - k; index += 1) {
    if (before[index - 1] >= k && after[index + 1] >= k) result.push(index);
  }
  return result;
}

const goodIndices = solve;
class Solution {
  goodIndices(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, goodIndices };
