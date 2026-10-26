'use strict';

// 1064. Fixed Point (Easy).
// Specification: https://leetcode.com/problems/fixed-point/description/
// O(log n) time, O(1) space; lower-bound search for the first arr[index] >= index in a strictly increasing array.
function solve(arr) {
  let left = 0;
  let right = arr.length;
  while (left < right) {
    const middle = left + Math.floor((right - left) / 2);
    if (arr[middle] < middle) left = middle + 1;
    else right = middle;
  }
  return left < arr.length && arr[left] === left ? left : -1;
}

const fixedPoint = solve;
class Solution {
  fixedPoint(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, fixedPoint };
