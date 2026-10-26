'use strict';

// 2762. Continuous Subarrays: count windows whose monotone-queue maximum and minimum differ by at most two.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const minima = [];
  const maxima = [];
  let minHead = 0;
  let maxHead = 0;
  let left = 0;
  let total = 0;
  for (let right = 0; right < nums.length; right += 1) {
    while (minima.length > minHead && nums[minima[minima.length - 1]] > nums[right]) minima.pop();
    while (maxima.length > maxHead && nums[maxima[maxima.length - 1]] < nums[right]) maxima.pop();
    minima.push(right);
    maxima.push(right);
    while (nums[maxima[maxHead]] - nums[minima[minHead]] > 2) {
      if (minima[minHead] === left) minHead += 1;
      if (maxima[maxHead] === left) maxHead += 1;
      left += 1;
    }
    total += right - left + 1;
  }
  return total;
}

const continuousSubarrays = solve;
class Solution {
  continuousSubarrays(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, continuousSubarrays };
