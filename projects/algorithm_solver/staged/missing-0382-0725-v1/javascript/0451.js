'use strict';

// 451. Sort Characters By Frequency. Descending frequencies with deterministic character-order ties.

function solve(s) {
  const counts = new Map();
  for (const char of s) counts.set(char, (counts.get(char) || 0) + 1);
  return Array.from(counts).sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0))
    .map(([char, count]) => char.repeat(count)).join('');
}

const frequencySort = solve;
class Solution {
  frequencySort(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, frequencySort };
