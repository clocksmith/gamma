'use strict';

// 179. Largest Number (Medium).
// Specification: https://leetcode.com/problems/largest-number/description/
function solve(nums) {
  const texts = nums.map(String);
  texts.sort((a, b) => (b + a).localeCompare(a + b));
  const result = texts.join('');
  return result[0] === '0' ? '0' : result;
}
const largestNumber = solve;
class Solution { largestNumber(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestNumber };
