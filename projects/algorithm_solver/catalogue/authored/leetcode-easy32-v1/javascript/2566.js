'use strict';

// 2566. Maximum Difference by Remapping a Digit (Easy).
// Specification: https://leetcode.com/problems/maximum-difference-by-remapping-a-digit/description/
// O(d) time and space for d digits. Leading zeroes are allowed in the minimum.
function solve(num) {
  const digits = String(num);
  let highTarget = '9';
  for (const character of digits) {
    if (character !== '9') {
      highTarget = character;
      break;
    }
  }
  const lowTarget = digits[0];
  let maximum = 0;
  let minimum = 0;
  for (const character of digits) {
    const digit = character.charCodeAt(0) - 48;
    maximum = maximum * 10 + (character === highTarget ? 9 : digit);
    minimum = minimum * 10 + (character === lowTarget ? 0 : digit);
  }
  return maximum - minimum;
}

const minMaxDifference = solve;
class Solution {
  minMaxDifference(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minMaxDifference };
