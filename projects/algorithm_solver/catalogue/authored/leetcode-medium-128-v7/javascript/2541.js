'use strict';

// 2541. Minimum Operations to Make Array Equal II: require divisible differences and balanced transfers between indices.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums1, nums2, k) {
  if (k === 0) return nums1.every((value, index) => value === nums2[index]) ? 0 : -1;
  let balance = 0;
  let operations = 0;
  for (let index = 0; index < nums1.length; index += 1) {
    const difference = nums1[index] - nums2[index];
    if (difference % k !== 0) return -1;
    balance += difference;
    if (difference > 0) operations += difference / k;
  }
  return balance === 0 ? operations : -1;
}

const minOperations = solve;
class Solution {
  minOperations(nums1, nums2, k) { return solve(nums1, nums2, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
