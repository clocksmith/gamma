'use strict';

// 1513. Number of Substrings With Only 1s: add the length of the current run of ones at each position.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s) {
  const modulus = 1000000007;
  let run = 0;
  let total = 0;
  for (const bit of s) {
    run = bit === '1' ? run + 1 : 0;
    total = (total + run) % modulus;
  }
  return total;
}

const numSub = solve;
class Solution {
  numSub(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numSub };
