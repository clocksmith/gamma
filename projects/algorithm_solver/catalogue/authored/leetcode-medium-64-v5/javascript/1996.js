'use strict';

// 1996. The Number of Weak Characters in the Game: scan decreasing attack with increasing defense inside equal-attack groups.
// O(n * log(n + 1)) time and O(n) auxiliary space; inputs are read-only.
function solve(properties) {
  const ordered = properties.slice().sort((a, b) => b[0] - a[0] || a[1] - b[1]);
  let strongestDefense = 0;
  let result = 0;
  for (const [, defense] of ordered) {
    if (defense < strongestDefense) result += 1;
    strongestDefense = Math.max(strongestDefense, defense);
  }
  return result;
}

const numberOfWeakCharacters = solve;
class Solution {
  numberOfWeakCharacters(properties) { return solve(properties); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfWeakCharacters };
