'use strict';

// 768. Max Chunks To Make Sorted II (Medium).
// Specification: https://leetcode.com/problems/max-chunks-to-make-sorted-ii/description/
function solve(arr) {
  const sorted = arr.slice().sort((a, b) => a - b);
  let chunks = 0;
  for (let i = 0; i < arr.length; i++) {
    const left = arr.slice(0, i + 1).sort((a, b) => a - b);
    const right = sorted.slice(0, i + 1);
    if (JSON.stringify(left) === JSON.stringify(right)) chunks++;
  }
  return chunks;
}
const maxChunksToSorted = solve;
class Solution { maxChunksToSorted(arr) { return solve(arr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxChunksToSorted };
