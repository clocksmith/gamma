'use strict';

// 769. Max Chunks To Make Sorted (Medium).
// Specification: https://leetcode.com/problems/max-chunks-to-make-sorted/description/
function solve(arr) {
  let chunks = 0; let maxValue = 0;
  for (let i = 0; i < arr.length; i++) { maxValue = Math.max(maxValue, arr[i]); if (maxValue === i) chunks++; }
  return chunks;
}
const maxChunksToSorted = solve;
class Solution { maxChunksToSorted(arr) { return solve(arr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxChunksToSorted };
