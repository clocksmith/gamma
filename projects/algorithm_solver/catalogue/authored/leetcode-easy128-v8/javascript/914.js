'use strict';

// 914. X of a Kind in a Deck of Cards (Easy).
// Specification: https://leetcode.com/problems/x-of-a-kind-in-a-deck-of-cards/description/
// O(n + u * log n) time, O(u) space; all frequencies must share a divisor of at least two.
function solve(deck) {
  const counts = new Map();
  for (const card of deck) counts.set(card, (counts.get(card) || 0) + 1);
  let divisor = 0;
  for (let count of counts.values()) {
    while (count !== 0) {
      const remainder = divisor % count;
      divisor = count;
      count = remainder;
    }
    if (divisor === 1) return false;
  }
  return divisor >= 2;
}

const hasGroupsSizeX = solve;
class Solution {
  hasGroupsSizeX(deck) { return solve(deck); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, hasGroupsSizeX };
