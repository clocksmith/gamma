'use strict';

// 2390. Removing Stars From a String: use a stack for the nearest surviving letter preceding each star.
// O(n) time and O(n) auxiliary and result space; inputs are read-only.
function solve(s) {
  const letters = [];
  for (const character of s) {
    if (character === '*') letters.pop();
    else letters.push(character);
  }
  return letters.join('');
}

const removeStars = solve;
class Solution {
  removeStars(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeStars };
