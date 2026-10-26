'use strict';

// 3079. Find the Sum of Encrypted Integers (Easy).
// Specification: https://leetcode.com/problems/find-the-sum-of-encrypted-integers/description/
// O(n log M) time, O(1) space; repeat each number's maximum digit arithmetically.
function solve(nums) {
  let total = 0;
  for (const value of nums) {
    let remaining = value;
    let maximum = 0;
    let ones = 0;
    while (remaining > 0) {
      maximum = Math.max(maximum, remaining % 10);
      ones = ones * 10 + 1;
      remaining = Math.floor(remaining / 10);
    }
    total += maximum * ones;
  }
  return total;
}

const sumOfEncryptedInt = solve;
class Solution {
  sumOfEncryptedInt(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumOfEncryptedInt };
