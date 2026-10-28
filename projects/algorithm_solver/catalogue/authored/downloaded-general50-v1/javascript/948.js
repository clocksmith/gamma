'use strict';

// 948. Bag of Tokens (Medium).
// Specification: https://leetcode.com/problems/bag-of-tokens/description/
function solve(tokens, power) {
  const sorted = tokens.slice().sort((a, b) => a - b);
  let left = 0; let right = sorted.length - 1; let score = 0; let best = 0;
  while (left <= right) {
    if (power >= sorted[left]) { power -= sorted[left]; left++; score++; best = Math.max(best, score); }
    else if (score > 0) { power += sorted[right]; right--; score--; }
    else break;
  }
  return best;
}
const bagOfTokensScore = solve;
class Solution { bagOfTokensScore(tokens, power) { return solve(tokens, power); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, bagOfTokensScore };
