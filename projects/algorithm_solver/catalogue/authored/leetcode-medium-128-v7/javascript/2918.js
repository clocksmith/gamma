'use strict';

// 2918. Minimum Equal Sum of Two Arrays After Replacing Zeros: compare minimum positive replacements and whether each side can increase.
// O(n + m) time and O(1) auxiliary space; inputs are read-only.
function solve(nums1, nums2) {
  let first = 0;
  let second = 0;
  let firstZeros = 0;
  let secondZeros = 0;
  for (const value of nums1) {
    first += value;
    if (value === 0) firstZeros += 1;
  }
  for (const value of nums2) {
    second += value;
    if (value === 0) secondZeros += 1;
  }
  first += firstZeros;
  second += secondZeros;
  if (firstZeros === 0 && first < second) return -1;
  if (secondZeros === 0 && second < first) return -1;
  return Math.max(first, second);
}

const minSum = solve;
class Solution {
  minSum(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSum };
