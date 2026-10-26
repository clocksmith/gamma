'use strict';

// 2040. Kth Smallest Product of Two Sorted Arrays. Binary search over products with sign-aware rank counts; O(n log m log R) time, O(1) auxiliary space. Inputs are preserved.

function solve(nums1, nums2, k) {
  function lowerBound(value) {
    let left = 0;
    let right = nums2.length;
    while (left < right) {
      const middle = Math.floor((left + right) / 2);
      if (nums2[middle] < value) left = middle + 1;
      else right = middle;
    }
    return left;
  }
  function upperBound(value) {
    let left = 0;
    let right = nums2.length;
    while (left < right) {
      const middle = Math.floor((left + right) / 2);
      if (nums2[middle] <= value) left = middle + 1;
      else right = middle;
    }
    return left;
  }
  function enough(limit) {
    let count = 0;
    for (const value of nums1) {
      if (value > 0) count += upperBound(Math.floor(limit / value));
      else if (value < 0) count += nums2.length - lowerBound(Math.ceil(limit / value));
      else if (limit >= 0) count += nums2.length;
      if (count >= k) return true;
    }
    return false;
  }
  const corners = [nums1[0] * nums2[0], nums1[0] * nums2[nums2.length - 1],
    nums1[nums1.length - 1] * nums2[0], nums1[nums1.length - 1] * nums2[nums2.length - 1]];
  let left = Math.min(...corners);
  let right = Math.max(...corners);
  while (left < right) {
    const middle = Math.floor((left + right) / 2);
    if (enough(middle)) right = middle;
    else left = middle + 1;
  }
  return left;
}

const kthSmallestProduct = solve;
class Solution {
  kthSmallestProduct(nums1, nums2, k) { return solve(nums1, nums2, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kthSmallestProduct };
