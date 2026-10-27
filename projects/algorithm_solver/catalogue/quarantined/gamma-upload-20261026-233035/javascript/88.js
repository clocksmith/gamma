'use strict';
// 88. Merge Sorted Array.
function solve(nums1, m, nums2, n) {
  let left = m - 1;
  let right = n - 1;
  let write = m + n - 1;
  while (right >= 0) {
    if (left >= 0 && nums1[left] > nums2[right]) nums1[write--] = nums1[left--];
    else nums1[write--] = nums2[right--];
  }
}
const merge = solve;
class Solution { merge(nums1, m, nums2, n) { solve(nums1, m, nums2, n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, merge };
