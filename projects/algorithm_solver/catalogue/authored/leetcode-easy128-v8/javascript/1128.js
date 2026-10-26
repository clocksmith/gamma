'use strict';

// 1128. Number of Equivalent Domino Pairs (Easy).
// Specification: https://leetcode.com/problems/number-of-equivalent-domino-pairs/description/
// O(n) time, O(1) space for digits 1 through 9; count prior unordered matches.
function solve(dominoes) {
  const counts = new Array(100).fill(0);
  let pairs = 0;
  for (const [first, second] of dominoes) {
    const key = Math.min(first, second) * 10 + Math.max(first, second);
    pairs += counts[key];
    counts[key]++;
  }
  return pairs;
}

const numEquivDominoPairs = solve;
class Solution {
  numEquivDominoPairs(dominoes) { return solve(dominoes); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numEquivDominoPairs };
