'use strict';

// 454. 4Sum II (Medium).
// Specification: https://leetcode.com/problems/4sum-ii/description/
function solve(nums1, nums2, nums3, nums4) {
  const sums = new Map();
  for (const a of nums1) { for (const b of nums2) sums.set(a + b, (sums.get(a + b) || 0) + 1); }
  let total = 0;
  for (const c of nums3) { for (const d of nums4) total += sums.get(-(c + d)) || 0; }
  return total;
}
const fourSumCount = solve;
class Solution { fourSumCount(nums1, nums2, nums3, nums4) { return solve(nums1, nums2, nums3, nums4); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, fourSumCount };
