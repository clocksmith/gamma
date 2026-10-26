'use strict';

// 1539. Kth Missing Positive Number (Easy).
// Specification: https://leetcode.com/problems/kth-missing-positive-number/description/
// O(log n) time, O(1) space; binary-search the missing-count boundary; preserve arr.
function solve(arr, k) {
  let low = 0;
  let high = arr.length;
  while (low < high) {
    const middle = low + Math.floor((high - low) / 2);
    if (arr[middle] - middle - 1 < k) low = middle + 1;
    else high = middle;
  }
  return low + k;
}

const findKthPositive = solve;
class Solution {
  findKthPositive(arr, k) { return solve(arr, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findKthPositive };
