'use strict';

// 1071. Greatest Common Divisor of Strings (Easy).
// Specification: https://leetcode.com/problems/greatest-common-divisor-of-strings/description/
// O(n + m) time and space; concatenation compatibility plus the GCD of lengths.
function solve(str1, str2) {
  if (str1 + str2 !== str2 + str1) return '';
  let first = str1.length;
  let second = str2.length;
  while (second !== 0) {
    const remainder = first % second;
    first = second;
    second = remainder;
  }
  return str1.slice(0, first);
}

const gcdOfStrings = solve;
class Solution {
  gcdOfStrings(str1, str2) { return solve(str1, str2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, gcdOfStrings };
