'use strict';

// 2525. Categorize Box According to Criteria (Easy).
// Specification: https://leetcode.com/problems/categorize-box-according-to-criteria/description/
// O(1) time and space; integer volume is at most 10^15, exact in Number.
function solve(length, width, height, mass) {
  const bulky = length >= 10000 || width >= 10000 || height >= 10000
    || length * width * height >= 1000000000;
  const heavy = mass >= 100;
  if (bulky && heavy) return 'Both';
  if (bulky) return 'Bulky';
  if (heavy) return 'Heavy';
  return 'Neither';
}

const categorizeBox = solve;
class Solution {
  categorizeBox(length, width, height, mass) { return solve(length, width, height, mass); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, categorizeBox };
