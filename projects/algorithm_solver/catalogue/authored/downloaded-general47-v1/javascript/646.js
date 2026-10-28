'use strict';

// 646. Maximum Length of Pair Chain (Medium).
// Specification: https://leetcode.com/problems/maximum-length-of-pair-chain/description/
function solve(pairs) {
  const sorted = pairs.slice().sort((a, b) => a[1] - b[1]);
  let count = 0; let currentEnd = -Infinity;
  for (const [start, end] of sorted) {
    if (start > currentEnd) { count++; currentEnd = end; }
  }
  return count;
}
const findLongestChain = solve;
class Solution { findLongestChain(pairs) { return solve(pairs); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findLongestChain };
