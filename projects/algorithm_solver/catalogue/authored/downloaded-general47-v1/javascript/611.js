'use strict';

// 611. Valid Triangle Number (Medium).
// Specification: https://leetcode.com/problems/valid-triangle-number/description/
function solve(nums) {
  const sorted = nums.slice().sort((a, b) => a - b);
  let count = 0;
  for (let k = sorted.length - 1; k >= 2; k--) {
    let left = 0; let right = k - 1;
    while (left < right) {
      if (sorted[left] + sorted[right] > sorted[k]) { count += right - left; right--; }
      else left++;
    }
  }
  return count;
}
const triangleNumber = solve;
class Solution { triangleNumber(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, triangleNumber };
