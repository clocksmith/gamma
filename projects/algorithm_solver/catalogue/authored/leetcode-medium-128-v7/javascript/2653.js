'use strict';

// 2653. Sliding Subarray Beauty: count negative values in each fixed window and locate the xth smallest.
// O(50 * n) time and O(n + 50) auxiliary space including the result; inputs are read-only.
function solve(nums, k, x) {
  const counts = new Int32Array(50);
  const result = [];
  for (let right = 0; right < nums.length; right += 1) {
    if (nums[right] < 0) counts[nums[right] + 50] += 1;
    if (right >= k && nums[right - k] < 0) counts[nums[right - k] + 50] -= 1;
    if (right + 1 < k) continue;
    let needed = x;
    let beauty = 0;
    for (let code = 0; code < counts.length; code += 1) {
      needed -= counts[code];
      if (needed <= 0) {
        beauty = code - 50;
        break;
      }
    }
    result.push(beauty);
  }
  return result;
}

const getSubarrayBeauty = solve;
class Solution {
  getSubarrayBeauty(nums, k, x) { return solve(nums, k, x); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getSubarrayBeauty };
