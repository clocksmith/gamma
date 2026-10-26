'use strict';

// 3754. Concatenate Non-Zero Digits and Multiply by Sum I (Easy).
// Specification: https://leetcode.com/problems/concatenate-non-zero-digits-and-multiply-by-sum-i/description/
// O(d) time, O(1) space; the result fits exactly in JavaScript Number, not necessarily int32.
function solve(n) {
  let remaining = n;
  let compact = 0;
  let digitSum = 0;
  let place = 1;
  while (remaining > 0) {
    const digit = remaining % 10;
    digitSum += digit;
    if (digit !== 0) {
      compact += digit * place;
      place *= 10;
    }
    remaining = Math.floor(remaining / 10);
  }
  return compact * digitSum;
}

const sumAndMultiply = solve;
class Solution {
  sumAndMultiply(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumAndMultiply };
