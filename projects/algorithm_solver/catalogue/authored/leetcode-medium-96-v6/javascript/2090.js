'use strict';

// 2090. K Radius Subarray Averages: slide an exact integer sum over every complete centered window.
// O(n) time and O(n) result space; inputs are read-only.
function solve(nums, k) {
  const width = 2 * k + 1;
  const result = new Array(nums.length).fill(-1);
  if (width > nums.length) return result;
  let total = 0;
  for (let index = 0; index < nums.length; index += 1) {
    total += nums[index];
    if (index >= width) total -= nums[index - width];
    if (index >= width - 1) result[index - k] = Math.floor(total / width);
  }
  return result;
}

const getAverages = solve;
class Solution {
  getAverages(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getAverages };
