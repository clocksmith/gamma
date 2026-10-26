'use strict';

// 1464. Maximum Product of Two Elements in an Array (Easy).
// Specification: https://leetcode.com/problems/maximum-product-of-two-elements-in-an-array/description/
// O(n) time, O(1) space; retain the two largest values at distinct indices.
function solve(nums) {
  let largest = 0;
  let second = 0;
  for (const value of nums) {
    if (value >= largest) {
      second = largest;
      largest = value;
    } else {
      second = Math.max(second, value);
    }
  }
  return (largest - 1) * (second - 1);
}

const maxProduct = solve;
class Solution {
  maxProduct(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProduct };
