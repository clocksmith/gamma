'use strict';

// 1898. Maximum Number of Removable Characters (Medium).
// Specification: https://leetcode.com/problems/maximum-number-of-removable-characters/description/
function isSubsequence(s, p, removed) {
  let j = 0;
  for (let i = 0; i < s.length && j < p.length; i++) {
    if (removed.has(i)) continue;
    if (s[i] === p[j]) j++;
  }
  return j === p.length;
}
function solve(s, p, removable) {
  let left = 0; let right = removable.length; let best = 0;
  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    const removed = new Set(removable.slice(0, mid));
    if (isSubsequence(s, p, removed)) { best = mid; left = mid + 1; }
    else right = mid - 1;
  }
  return best;
}
const maximumRemovals = solve;
class Solution { maximumRemovals(s, p, removable) { return solve(s, p, removable); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumRemovals };
