'use strict';
// 349. Intersection of Two Arrays.
function solve(nums1, nums2) {
  const right = new Set(nums2);
  return [...new Set(nums1)].filter(value => right.has(value));
}
const intersection = solve;
class Solution { intersection(nums1, nums2) { return solve(nums1, nums2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, intersection };
