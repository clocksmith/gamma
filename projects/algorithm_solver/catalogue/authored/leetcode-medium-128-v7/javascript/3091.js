'use strict';

// 3091. Apply Operations to Make Sum of Array Greater Than or Equal to k: balance increments of one value against the number of copies needed to reach k.
// O(sqrt(k)) time and O(1) auxiliary space; inputs are read-only.
function solve(k) {
  let best = k - 1;
  const bound = Math.floor(Math.sqrt(k)) + 1;
  for (let value = 1; value <= bound; value += 1) {
    const copies = Math.ceil(k / value);
    best = Math.min(best, value + copies - 2);
  }
  return best;
}

const minOperations = solve;
class Solution {
  minOperations(k) { return solve(k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
