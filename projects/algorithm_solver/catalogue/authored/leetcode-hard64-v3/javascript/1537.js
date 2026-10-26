'use strict';

// 1537. Get the Maximum Score: two-pointer accumulation between shared values; O(n+m) time and O(1) space.

function solve(nums1, nums2) {
  let first = 0;
  let second = 0;
  let firstSum = 0;
  let secondSum = 0;
  let total = 0;
  while (first < nums1.length || second < nums2.length) {
    if (second === nums2.length || (first < nums1.length && nums1[first] < nums2[second])) {
      firstSum += nums1[first];
      first += 1;
    } else if (first === nums1.length || nums2[second] < nums1[first]) {
      secondSum += nums2[second];
      second += 1;
    } else {
      total += Math.max(firstSum, secondSum) + nums1[first];
      firstSum = 0;
      secondSum = 0;
      first += 1;
      second += 1;
    }
  }
  // Compare unreduced sums; the declared inputs keep them within safe integers.
  return (total + Math.max(firstSum, secondSum)) % 1000000007;
}

const maxSum = solve;
class Solution {
  maxSum(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSum };
