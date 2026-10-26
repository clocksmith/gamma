'use strict';

// 1287. Element Appearing More Than 25% In Sorted Array (Easy).
// Specification: https://leetcode.com/problems/element-appearing-more-than-25-in-sorted-array/description/
// O(n) time, O(1) space; preserve the sorted input.
function solve(arr) {
  const offset = Math.floor(arr.length / 4);
  for (let index = 0; index + offset < arr.length; index++) {
    if (arr[index] === arr[index + offset]) return arr[index];
  }
  return arr[0];
}

const findSpecialInteger = solve;
class Solution {
  findSpecialInteger(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findSpecialInteger };
