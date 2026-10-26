'use strict';

// 2350. Shortest Impossible Sequence of Rolls. Greedily finish complete alphabet blocks; O(n+k) time and O(k) space. Inputs are preserved.

function solve(rolls, k) {
  const seen = new Set();
  let answer = 1;
  for (const value of rolls) {
    seen.add(value);
    if (seen.size === k) {
      answer += 1;
      seen.clear();
    }
  }
  return answer;
}

const shortestSequence = solve;
class Solution {
  shortestSequence(rolls, k) { return solve(rolls, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, shortestSequence };
