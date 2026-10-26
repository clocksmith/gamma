'use strict';

// 1018. Binary Prefix Divisible By 5 (Easy).
// Specification: https://leetcode.com/problems/binary-prefix-divisible-by-5/description/
// O(n) time and output space; retain only the prefix remainder modulo five.
function solve(nums) {
  let remainder = 0;
  const result = [];
  for (const digit of nums) {
    remainder = (2 * remainder + digit) % 5;
    result.push(remainder === 0);
  }
  return result;
}

const prefixesDivBy5 = solve;
class Solution {
  prefixesDivBy5(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, prefixesDivBy5 };
