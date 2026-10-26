'use strict';

// 941. Valid Mountain Array (Easy).
// Specification: https://leetcode.com/problems/valid-mountain-array/description/
// O(n) time, O(1) space; require a nonempty strictly increasing and decreasing segment.
function solve(arr) {
  if (arr.length < 3) return false;
  let index = 1;
  while (index < arr.length && arr[index] > arr[index - 1]) index++;
  if (index === 1 || index === arr.length) return false;
  while (index < arr.length && arr[index] < arr[index - 1]) index++;
  return index === arr.length;
}

const validMountainArray = solve;
class Solution {
  validMountainArray(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, validMountainArray };
