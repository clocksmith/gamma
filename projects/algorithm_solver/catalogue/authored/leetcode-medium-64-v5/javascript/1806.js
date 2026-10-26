'use strict';

// 1806. Minimum Number of Operations to Reinitialize a Permutation: follow the nontrivial index-one cycle of the perfect shuffle.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(n) {
  let position = 1;
  let steps = 0;
  do {
    position = position % 2 === 0 ? position / 2 : n / 2 + (position - 1) / 2;
    steps += 1;
  } while (position !== 1);
  return steps;
}

const reinitializePermutation = solve;
class Solution {
  reinitializePermutation(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reinitializePermutation };
