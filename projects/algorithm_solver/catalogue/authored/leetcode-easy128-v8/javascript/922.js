'use strict';

// 922. Sort Array By Parity II (Easy).
// Specification: https://leetcode.com/problems/sort-array-by-parity-ii/description/
// O(n) time and space; fill even and odd result indices in original encounter order.
function solve(nums) {
  const result = new Array(nums.length);
  let evenIndex = 0;
  let oddIndex = 1;
  for (const value of nums) {
    if (value % 2 === 0) {
      result[evenIndex] = value;
      evenIndex += 2;
    } else {
      result[oddIndex] = value;
      oddIndex += 2;
    }
  }
  return result;
}

const sortArrayByParityII = solve;
class Solution {
  sortArrayByParityII(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sortArrayByParityII };
