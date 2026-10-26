'use strict';

// 3732. Maximum Product of Three Elements After One Replacement.
// O(n) time and O(1) auxiliary space; replace a third index using the sign that makes the product nonnegative.
function solve(nums) {
  let largest = 0;
  let second = 0;
  for (const entry of nums) {
    const value = Math.abs(entry);
    if (value >= largest) {
      second = largest;
      largest = value;
    } else if (value > second) {
      second = value;
    }
  }
  return largest * second * 100000;
}

const maxProduct = solve;
class Solution {
  maxProduct(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProduct };
