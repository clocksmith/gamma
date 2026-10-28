'use strict';

// 658. Find K Closest Elements (Medium).
// Specification: https://leetcode.com/problems/find-k-closest-elements/description/
function solve(arr, k, x) {
  let left = 0; let right = arr.length - k;
  while (left < right) {
    const mid = Math.floor((left + right) / 2);
    if (x - arr[mid] > arr[mid + k] - x) left = mid + 1;
    else right = mid;
  }
  return arr.slice(left, left + k);
}
const findClosestElements = solve;
class Solution { findClosestElements(arr, k, x) { return solve(arr, k, x); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findClosestElements };
