'use strict';

// 1122. Relative Sort Array (Easy).
// Specification: https://leetcode.com/problems/relative-sort-array/description/
// O(n + m + u log u) time, O(n + u) space; ordered groups first, remaining values ascending.
function solve(arr1, arr2) {
  const counts = new Map();
  for (const value of arr1) counts.set(value, (counts.get(value) || 0) + 1);
  const result = [];
  for (const value of arr2) {
    for (let count = counts.get(value) || 0; count > 0; count--) result.push(value);
    counts.delete(value);
  }
  const remaining = Array.from(counts.keys()).sort((a, b) => a - b);
  for (const value of remaining) {
    for (let count = counts.get(value); count > 0; count--) result.push(value);
  }
  return result;
}

const relativeSortArray = solve;
class Solution {
  relativeSortArray(arr1, arr2) { return solve(arr1, arr2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, relativeSortArray };
