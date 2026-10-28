'use strict';

// 950. Reveal Cards In Increasing Order (Medium).
// Specification: https://leetcode.com/problems/reveal-cards-in-increasing-order/description/
function solve(deck) {
  const sorted = deck.slice().sort((a, b) => a - b);
  const result = new Array(deck.length);
  const queue = deck.map((_, i) => i);
  for (const card of sorted) {
    const idx = queue.shift();
    result[idx] = card;
    if (queue.length > 0) queue.push(queue.shift());
  }
  return result;
}
const deckRevealedIncreasing = solve;
class Solution { deckRevealedIncreasing(deck) { return solve(deck); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, deckRevealedIncreasing };
