'use strict';

// 3536. Maximum Product of Two Digits (Easy).
// Specification: https://leetcode.com/problems/maximum-product-of-two-digits/description/
// O(log n) time, O(1) space; retain the two largest digit occurrences.
function solve(n) {
  let largest = 0;
  let second = 0;
  while (n > 0) {
    const digit = n % 10;
    if (digit >= largest) {
      second = largest;
      largest = digit;
    } else if (digit > second) {
      second = digit;
    }
    n = Math.floor(n / 10);
  }
  return largest * second;
}

const maxProduct = solve;
class Solution {
  maxProduct(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProduct };
