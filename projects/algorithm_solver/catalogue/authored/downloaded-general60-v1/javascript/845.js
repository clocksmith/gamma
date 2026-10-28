'use strict';

// 845. Longest Mountain in Array (Medium).
// Specification: https://leetcode.com/problems/longest-mountain-in-array/description/
function solve(arr) {
  let best = 0;
  let i = 1;
  while (i < arr.length - 1) {
    if (arr[i] > arr[i - 1] && arr[i] > arr[i + 1]) {
      let left = i - 1;
      while (left > 0 && arr[left] > arr[left - 1]) left--;
      let right = i + 1;
      while (right < arr.length - 1 && arr[right] > arr[right + 1]) right++;
      best = Math.max(best, right - left + 1);
      i = right;
    } else i++;
  }
  return best;
}
const longestMountain = solve;
class Solution { longestMountain(arr) { return solve(arr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestMountain };
