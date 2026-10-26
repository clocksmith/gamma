'use strict';

// 1640. Check Array Formation Through Concatenation (Easy).
// Specification: https://leetcode.com/problems/check-array-formation-through-concatenation/description/
// O(n) expected time, O(p) space for p pieces; preserve arr, pieces, and their rows.
function solve(arr, pieces) {
  const byFirstValue = new Map();
  for (const piece of pieces) byFirstValue.set(piece[0], piece);
  let index = 0;
  while (index < arr.length) {
    const piece = byFirstValue.get(arr[index]);
    if (piece === undefined) return false;
    for (const value of piece) {
      if (index >= arr.length || arr[index] !== value) return false;
      index++;
    }
  }
  return true;
}

const canFormArray = solve;
class Solution {
  canFormArray(arr, pieces) { return solve(arr, pieces); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canFormArray };
