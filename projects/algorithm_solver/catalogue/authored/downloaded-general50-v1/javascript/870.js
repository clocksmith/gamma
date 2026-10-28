'use strict';

// 870. Advantage Shuffle (Medium).
// Specification: https://leetcode.com/problems/advantage-shuffle/description/
function solve(nums1, nums2) {
  const sorted = nums1.slice().sort((a, b) => a - b);
  const order = nums2.map((v, i) => i).sort((a, b) => nums2[a] - nums2[b]);
  const result = new Array(nums1.length);
  let left = 0; let right = sorted.length - 1;
  for (let k = order.length - 1; k >= 0; k--) {
    const idx = order[k];
    if (sorted[right] > nums2[idx]) { result[idx] = sorted[right]; right--; }
    else { result[idx] = sorted[left]; left++; }
  }
  return result;
}
const advantageCount = solve;
class Solution { advantageCount(nums1, nums2) { return solve(nums1, nums2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, advantageCount };
