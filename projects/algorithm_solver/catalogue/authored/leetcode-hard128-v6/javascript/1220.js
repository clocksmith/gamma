'use strict';

// 1220. Count Vowels Permutation.
// Five-state transition DP; O(n) time and O(1) space.

function solve(n) {
  const modulus = 1000000007;
  let a = 1, e = 1, i = 1, o = 1, u = 1;
  for (let length = 1; length < n; length += 1) {
    [a, e, i, o, u] = [(e + i + u) % modulus, (a + i) % modulus, (e + o) % modulus, i, (i + o) % modulus];
  }
  return (a + e + i + o + u) % modulus;
}

const countVowelPermutation = solve;
class Solution {
  countVowelPermutation(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countVowelPermutation };
