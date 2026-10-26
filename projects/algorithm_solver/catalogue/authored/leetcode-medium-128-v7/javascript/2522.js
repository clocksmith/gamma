'use strict';

// 2522. Partition String Into Substrings With Values at Most K: extend each decimal piece greedily until the next digit would exceed k.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s, k) {
  let pieces = 1;
  let value = 0;
  for (const character of s) {
    const digit = character.charCodeAt(0) - 48;
    if (digit > k) return -1;
    if (value * 10 + digit > k) {
      pieces += 1;
      value = digit;
    } else {
      value = value * 10 + digit;
    }
  }
  return pieces;
}

const minimumPartition = solve;
class Solution {
  minimumPartition(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumPartition };
