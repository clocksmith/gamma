'use strict';

// 373. Find K Pairs with Smallest Sums (Medium).
// Specification: https://leetcode.com/problems/find-k-pairs-with-smallest-sums/description/
function solve(nums1, nums2, k) {
  const pairs = [];
  for (const a of nums1) { for (const b of nums2) pairs.push([a, b]); }
  pairs.sort((a, b) => (a[0] + a[1]) - (b[0] + b[1]) || a[0] - b[0] || a[1] - b[1]);
  return pairs.slice(0, k);
}
const kSmallestPairs = solve;
class Solution { kSmallestPairs(nums1, nums2, k) { return solve(nums1, nums2, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, kSmallestPairs };
