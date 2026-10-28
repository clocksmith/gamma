'use strict';

// 763. Partition Labels (Medium).
// Specification: https://leetcode.com/problems/partition-labels/description/
function solve(s) {
  const last = {};
  for (let i = 0; i < s.length; i++) last[s[i]] = i;
  const result = [];
  let start = 0; let end = 0;
  for (let i = 0; i < s.length; i++) {
    end = Math.max(end, last[s[i]]);
    if (i === end) { result.push(end - start + 1); start = i + 1; }
  }
  return result;
}
const partitionLabels = solve;
class Solution { partitionLabels(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, partitionLabels };
