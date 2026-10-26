'use strict';

// 455. Assign Cookies (Easy).
// Specification: https://leetcode.com/problems/assign-cookies/description/
// O(n log n + m log m) time, O(n + m) space; sort copies and satisfy least-greedy children first.
function solve(g, s) {
  const greed = g.slice().sort((a, b) => a - b);
  const cookies = s.slice().sort((a, b) => a - b);
  let child = 0;
  for (const size of cookies) {
    if (child < greed.length && size >= greed[child]) child++;
  }
  return child;
}

const findContentChildren = solve;
class Solution {
  findContentChildren(g, s) { return solve(g, s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findContentChildren };
