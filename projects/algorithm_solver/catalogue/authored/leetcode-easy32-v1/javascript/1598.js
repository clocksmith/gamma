'use strict';

// 1598. Crawler Log Folder (Easy).
// Specification: https://leetcode.com/problems/crawler-log-folder/description/
// O(n) time, O(1) auxiliary space. Only track depth; preserve the log.
function solve(logs) {
  let depth = 0;
  for (const operation of logs) {
    if (operation === '../') {
      depth = Math.max(0, depth - 1);
    } else if (operation !== './') {
      depth++;
    }
  }
  return depth;
}

const minOperations = solve;
class Solution {
  minOperations(logs) { return solve(logs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
