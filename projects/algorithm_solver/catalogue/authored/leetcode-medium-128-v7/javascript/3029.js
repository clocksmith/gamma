'use strict';

// 3029. Minimum Time to Revert Word to Initial State I: find the first allowed removal length leaving a suffix equal to the initial prefix.
// O(n * n) worst-case time and O(n) auxiliary space; inputs are read-only.
function solve(word, k) {
  for (let removed = k; removed < word.length; removed += k) {
    if (word.startsWith(word.slice(removed))) return removed / k;
  }
  return Math.ceil(word.length / k);
}

const minimumTimeToInitialState = solve;
class Solution {
  minimumTimeToInitialState(word, k) { return solve(word, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumTimeToInitialState };
