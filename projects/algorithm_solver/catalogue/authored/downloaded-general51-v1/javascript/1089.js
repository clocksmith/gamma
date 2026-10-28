'use strict';

// 1089. Duplicate Zeros (Easy).
// Specification: https://leetcode.com/problems/duplicate-zeros/description/
function solve(arr) {
  const result = [];
  for (const value of arr) {
    if (result.length >= arr.length) break;
    result.push(value);
    if (value === 0 && result.length < arr.length) result.push(0);
  }
  return result;
}
const duplicateZeros = solve;
class Solution { duplicateZeros(arr) { return solve(arr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, duplicateZeros };
