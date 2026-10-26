'use strict';

// 2578. Split With Minimum Sum (Easy).
// Specification: https://leetcode.com/problems/split-with-minimum-sum/description/
// O(d log d) time, O(d) space; distribute sorted digits alternately to minimize place values.
function solve(num) {
  const digits = String(num).split('').sort();
  const parts = [0, 0];
  for (let index = 0; index < digits.length; index++) {
    const part = index % 2;
    parts[part] = parts[part] * 10 + Number(digits[index]);
  }
  return parts[0] + parts[1];
}

const splitNum = solve;
class Solution {
  splitNum(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, splitNum };
