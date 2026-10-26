'use strict';

// 2645. Minimum Additions to Make Valid String: start a new abc block whenever the next letter does not increase.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(word) {
  let blocks = 1;
  for (let index = 1; index < word.length; index += 1) {
    if (word[index] <= word[index - 1]) blocks += 1;
  }
  return 3 * blocks - word.length;
}

const addMinimum = solve;
class Solution {
  addMinimum(word) { return solve(word); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, addMinimum };
