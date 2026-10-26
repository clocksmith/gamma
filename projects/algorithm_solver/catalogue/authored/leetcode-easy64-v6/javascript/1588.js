'use strict';

// 1588. Sum of All Odd Length Subarrays (Easy).
// Specification: https://leetcode.com/problems/sum-of-all-odd-length-subarrays/description/
// O(n) time, O(1) space; count odd-length windows containing each index; preserve arr.
function solve(arr) {
  let result = 0;
  for (let index = 0; index < arr.length; index++) {
    const containingWindows = (index + 1) * (arr.length - index);
    const oddWindows = Math.floor((containingWindows + 1) / 2);
    result += arr[index] * oddWindows;
  }
  return result;
}

const sumOddLengthSubarrays = solve;
class Solution {
  sumOddLengthSubarrays(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumOddLengthSubarrays };
