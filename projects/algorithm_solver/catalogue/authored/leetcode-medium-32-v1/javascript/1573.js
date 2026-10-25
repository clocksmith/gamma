'use strict';

// 1573. Number of Ways to Split a String: count the two gaps separating equal groups of ones.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(s) {
  const modulus = 1_000_000_007;
  const ones = [];
  for (let index = 0; index < s.length; index += 1) {
    if (s[index] === '1') ones.push(index);
  }
  if (ones.length % 3 !== 0) return 0;
  if (ones.length === 0) {
    return ((s.length - 1) * (s.length - 2) / 2) % modulus;
  }
  const group = ones.length / 3;
  const firstGap = ones[group] - ones[group - 1];
  const secondGap = ones[2 * group] - ones[2 * group - 1];
  return firstGap * secondGap % modulus;
}

const numWays = solve;
class Solution {
  numWays(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numWays };
