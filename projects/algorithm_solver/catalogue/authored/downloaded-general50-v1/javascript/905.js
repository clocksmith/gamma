'use strict';

// 905. Sort Array By Parity (Easy).
// Specification: https://leetcode.com/problems/sort-array-by-parity/description/
function solve(nums) {
  return nums.filter((v) => v % 2 === 0).concat(nums.filter((v) => v % 2 !== 0));
}
const sortArrayByParity = solve;
class Solution { sortArrayByParity(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, sortArrayByParity };
