'use strict';

// 2605. Form Smallest Number From Two Digit Arrays (Easy).
// Specification: https://leetcode.com/problems/form-smallest-number-from-two-digit-arrays/description/
function solve(nums1, nums2) {
  const set1 = new Set(nums1);
  let common = null;
  for (const d of nums2) if (set1.has(d) && (common === null || d < common)) common = d;
  if (common !== null) return common;
  const m1 = Math.min(...nums1); const m2 = Math.min(...nums2);
  return Math.min(m1, m2) * 10 + Math.max(m1, m2);
}
const minNumber = solve;
class Solution { minNumber(nums1, nums2) { return solve(nums1, nums2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minNumber };
