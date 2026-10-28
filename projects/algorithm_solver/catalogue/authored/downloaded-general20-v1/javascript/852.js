'use strict';

// 852. Peak Index in a Mountain Array (Medium).
// Specification: https://leetcode.com/problems/peak-index-in-a-mountain-array/description/
function solve(arr) {
  let left = 0;
  let right = arr.length - 1;
  while (left < right) {
    const middle = Math.floor((left + right) / 2);
    if (arr[middle] < arr[middle + 1]) left = middle + 1;
    else right = middle;
  }
  return left;
}

const peakIndexInMountainArray = solve;
class Solution {
  peakIndexInMountainArray(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, peakIndexInMountainArray };
