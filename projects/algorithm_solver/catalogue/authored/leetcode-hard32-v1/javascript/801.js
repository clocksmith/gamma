'use strict';

// 801. Minimum Swaps To Make Sequences Increasing.
// O(n) time, O(1) space. Only costs change; both input arrays are preserved.
function solve(nums1, nums2) {
  let keep = 0;
  let swap = 1;
  const impossible = nums1.length + 1;
  for (let index = 1; index < nums1.length; index += 1) {
    let nextKeep = impossible;
    let nextSwap = impossible;
    if (nums1[index - 1] < nums1[index] && nums2[index - 1] < nums2[index]) {
      nextKeep = keep;
      nextSwap = swap + 1;
    }
    if (nums1[index - 1] < nums2[index] && nums2[index - 1] < nums1[index]) {
      nextKeep = Math.min(nextKeep, swap);
      nextSwap = Math.min(nextSwap, keep + 1);
    }
    keep = nextKeep;
    swap = nextSwap;
  }
  return Math.min(keep, swap);
}

const minSwap = solve;
class Solution {
  minSwap(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSwap };
