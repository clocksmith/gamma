'use strict';
// 350. Intersection of Two Arrays II.
function solve(nums1, nums2) {
  const counts = new Map();
  for (const value of nums1) counts.set(value, (counts.get(value) || 0) + 1);
  const result = [];
  for (const value of nums2) if ((counts.get(value) || 0) > 0) {
    result.push(value); counts.set(value, counts.get(value) - 1);
  }
  return result;
}
const intersect = solve;
class Solution { intersect(nums1, nums2) { return solve(nums1, nums2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, intersect };
