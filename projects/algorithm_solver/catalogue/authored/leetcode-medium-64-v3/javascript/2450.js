'use strict';

// 2450. Number of Distinct Binary Strings After Applying Operations: count the independent fixed-width flip vectors.
// O(log(n + 1)) modular arithmetic operations and O(1) auxiliary space; inputs are read-only.
function solve(s, k) {
  // The leftmost changed position makes the n-k+1 flip vectors independent.
  const modulus = 1000000007n;
  let power = s.length - k + 1;
  let base = 2n;
  let answer = 1n;
  while (power > 0) {
    if (power % 2 !== 0) answer = answer * base % modulus;
    base = base * base % modulus;
    power = Math.floor(power / 2);
  }
  return Number(answer);
}

const countDistinctStrings = solve;
class Solution {
  countDistinctStrings(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countDistinctStrings };
