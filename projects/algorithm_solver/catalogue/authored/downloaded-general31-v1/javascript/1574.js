'use strict';

// 1574. Shortest Subarray to be Removed to Make Array Sorted (Medium).
// Specification: https://leetcode.com/problems/shortest-subarray-to-be-removed-to-make-array-sorted/description/
function solve(arr) {
  const n = arr.length;
  let left = 0;
  while (left + 1 < n && arr[left] <= arr[left + 1]) left++;
  if (left === n - 1) return 0;
  let right = n - 1;
  while (right > 0 && arr[right - 1] <= arr[right]) right--;
  let best = Math.min(n - left - 1, right);
  let i = 0; let j = right;
  while (i <= left && j < n) {
    if (arr[i] <= arr[j]) { best = Math.min(best, j - i - 1); i++; }
    else j++;
  }
  return best;
}
const findLengthOfShortestSubarray = solve;
class Solution { findLengthOfShortestSubarray(arr) { return solve(arr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findLengthOfShortestSubarray };
