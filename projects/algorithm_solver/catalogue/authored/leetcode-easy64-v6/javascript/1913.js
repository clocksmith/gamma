'use strict';

// 1913. Maximum Product Difference Between Two Pairs (Easy).
// Specification: https://leetcode.com/problems/maximum-product-difference-between-two-pairs/description/
// O(n) time, O(1) space; keep two extrema with multiplicity; preserve nums.
function solve(nums) {
  let smallest = Infinity;
  let secondSmallest = Infinity;
  let largest = -Infinity;
  let secondLargest = -Infinity;
  for (const value of nums) {
    if (value <= smallest) {
      secondSmallest = smallest;
      smallest = value;
    } else if (value < secondSmallest) {
      secondSmallest = value;
    }
    if (value >= largest) {
      secondLargest = largest;
      largest = value;
    } else if (value > secondLargest) {
      secondLargest = value;
    }
  }
  return largest * secondLargest - smallest * secondSmallest;
}

const maxProductDifference = solve;
class Solution {
  maxProductDifference(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProductDifference };
