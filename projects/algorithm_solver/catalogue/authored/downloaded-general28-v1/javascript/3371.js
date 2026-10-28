'use strict';

// 3371. Identify the Largest Outlier in an Array (Medium).
// Specification: https://leetcode.com/problems/identify-the-largest-outlier-in-an-array/description/
function solve(nums) {
  const total = nums.reduce((a, b) => a + b, 0);
  const freq = new Map();
  for (const x of nums) freq.set(x, (freq.get(x) || 0) + 1);
  let ans = -Infinity;
  for (const x of nums) {
    const rest = total - x;
    if (rest % 2 !== 0) continue;
    const sumVal = rest / 2;
    const need = sumVal === x ? 2 : 1;
    if ((freq.get(sumVal) || 0) >= need) ans = Math.max(ans, x);
  }
  return ans;
}
const getLargestOutlier = solve;
class Solution { getLargestOutlier(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, getLargestOutlier };
