'use strict';

// 800. Similar RGB Color (Easy).
// Specification: https://leetcode.com/problems/similar-rgb-color/description/
// O(1) time and space; round each hexadecimal channel to its nearest multiple of 17.
function solve(color) {
  const result = ['#'];
  for (let index = 1; index < color.length; index += 2) {
    const channel = Number.parseInt(color.slice(index, index + 2), 16);
    const digit = Math.floor((channel + 8) / 17).toString(16);
    result.push(digit, digit);
  }
  return result.join('');
}

const similarRGB = solve;
class Solution {
  similarRGB(color) { return solve(color); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, similarRGB };
