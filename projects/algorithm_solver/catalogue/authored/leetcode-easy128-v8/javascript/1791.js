'use strict';

// 1791. Find Center of Star Graph (Easy).
// Specification: https://leetcode.com/problems/find-center-of-star-graph/description/
// O(1) time and space; the first two edges share the guaranteed star center.
function solve(edges) {
  const candidate = edges[0][0];
  return candidate === edges[1][0] || candidate === edges[1][1] ? candidate : edges[0][1];
}

const findCenter = solve;
class Solution {
  findCenter(edges) { return solve(edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findCenter };
