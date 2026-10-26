'use strict';

// 3545. Minimum Deletions for At Most K Distinct Characters (Easy).
// Specification: https://leetcode.com/problems/minimum-deletions-for-at-most-k-distinct-characters/description/
// O(n) time, O(1) alphabet space; preserve s.
function solve(s, k) {
  const counts = new Array(26).fill(0);

  for (const character of s) counts[character.charCodeAt(0) - 97]++;
  counts.sort((left, right) => right - left);
  let deletions = 0;
  for (let index = k; index < counts.length; index++) deletions += counts[index];
  return deletions;
}

const minDeletion = solve;
class Solution {
  minDeletion(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minDeletion };
