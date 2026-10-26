'use strict';

// 2875. Minimum Size Subarray in Infinite Array: remove complete positive-sum periods and find the shortest circular remainder window.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums, target) {
  let period = 0;
  for (const value of nums) period += value;
  const cycles = Math.floor(target / period);
  const remainder = target % period;
  const base = cycles * nums.length;
  if (remainder === 0) return base;
  let left = 0;
  let total = 0;
  let best = nums.length + 1;
  for (let right = 0; right < 2 * nums.length; right += 1) {
    total += nums[right % nums.length];
    while (total > remainder) {
      total -= nums[left % nums.length];
      left += 1;
    }
    if (total === remainder) best = Math.min(best, right - left + 1);
  }
  return best <= nums.length ? base + best : -1;
}

const minSizeSubarray = solve;
class Solution {
  minSizeSubarray(nums, target) { return solve(nums, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSizeSubarray };
