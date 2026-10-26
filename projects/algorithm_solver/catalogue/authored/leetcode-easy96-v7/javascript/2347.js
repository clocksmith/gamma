'use strict';

// 2347. Best Poker Hand (Easy).
// Specification: https://leetcode.com/problems/best-poker-hand/description/
// O(1) time and space for five cards; prioritize Flush, Three of a Kind, Pair, High Card.
function solve(ranks, suits) {
  if (suits.every(suit => suit === suits[0])) return 'Flush';
  const counts = new Map();
  let largest = 0;
  for (const rank of ranks) {
    const count = (counts.get(rank) || 0) + 1;
    counts.set(rank, count);
    largest = Math.max(largest, count);
  }
  if (largest >= 3) return 'Three of a Kind';
  if (largest >= 2) return 'Pair';
  return 'High Card';
}

const bestHand = solve;
class Solution {
  bestHand(ranks, suits) { return solve(ranks, suits); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, bestHand };
