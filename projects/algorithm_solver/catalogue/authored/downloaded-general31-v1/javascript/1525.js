'use strict';

// 1525. Number of Good Ways to Split a String (Medium).
// Specification: https://leetcode.com/problems/number-of-good-ways-to-split-a-string/description/
function solve(s) {
  const leftCounts = new Map(); const rightCounts = new Map();
  for (const ch of s) rightCounts.set(ch, (rightCounts.get(ch) || 0) + 1);
  let count = 0;
  for (let i = 0; i < s.length - 1; i++) {
    const ch = s[i];
    leftCounts.set(ch, (leftCounts.get(ch) || 0) + 1);
    const remaining = rightCounts.get(ch) - 1;
    if (remaining === 0) rightCounts.delete(ch); else rightCounts.set(ch, remaining);
    if (leftCounts.size === rightCounts.size) count++;
  }
  return count;
}
const numSplits = solve;
class Solution { numSplits(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numSplits };
