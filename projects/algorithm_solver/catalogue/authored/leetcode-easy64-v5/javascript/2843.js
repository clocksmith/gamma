'use strict';

// 2843. Count Symmetric Integers (Easy).
// Specification: https://leetcode.com/problems/count-symmetric-integers/description/
// O((high - low + 1) * d) time, O(d) space; d is maximum decimal digit count.
function solve(low, high) {
  let count = 0;
  for (let value = low; value <= high; value++) {
    const digits = String(value);
    if (digits.length % 2 !== 0) continue;
    const half = digits.length / 2;
    let difference = 0;
    for (let index = 0; index < half; index++) {
      difference += digits.charCodeAt(index) - digits.charCodeAt(index + half);
    }
    if (difference === 0) count++;
  }
  return count;
}

const countSymmetricIntegers = solve;
class Solution {
  countSymmetricIntegers(low, high) { return solve(low, high); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSymmetricIntegers };
