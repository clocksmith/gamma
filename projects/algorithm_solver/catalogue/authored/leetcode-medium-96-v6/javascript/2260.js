'use strict';

// 2260. Minimum Consecutive Cards to Pick Up: compare each repeated card with its nearest previous occurrence.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
function solve(cards) {
  const previous = new Map();
  let best = cards.length + 1;
  for (let index = 0; index < cards.length; index += 1) {
    const value = cards[index];
    if (previous.has(value)) best = Math.min(best, index - previous.get(value) + 1);
    previous.set(value, index);
  }
  return best <= cards.length ? best : -1;
}

const minimumCardPickup = solve;
class Solution {
  minimumCardPickup(cards) { return solve(cards); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumCardPickup };
