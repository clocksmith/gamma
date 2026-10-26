'use strict';

// 482. License Key Formatting (Easy).
// Specification: https://leetcode.com/problems/license-key-formatting/description/
// O(n) time and space; collect uppercase groups from the right, ignoring old separators.
function solve(s, k) {
  const result = [];
  let count = 0;
  for (let index = s.length - 1; index >= 0; index--) {
    if (s[index] === '-') continue;
    if (count === k) {
      result.push('-');
      count = 0;
    }
    result.push(s[index].toUpperCase());
    count++;
  }
  return result.reverse().join('');
}

const licenseKeyFormatting = solve;
class Solution {
  licenseKeyFormatting(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, licenseKeyFormatting };
