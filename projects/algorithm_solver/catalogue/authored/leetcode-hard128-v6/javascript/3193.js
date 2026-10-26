'use strict';

// 3193. Count the Number of Inversions.
// Prefix inversion DP with a sliding transition sum and immediate constraint filtering; O(n*C) time and O(C) space. Inputs are preserved.

function solve(n, requirements) {
  const modulus = 1000000007, required = new Map(requirements);
  let cap = 0;
  for (const [end, count] of requirements) { if (count > (end + 1) * end / 2) return 0; cap = Math.max(cap, count); }
  if (requirements.length === 0) cap = n * (n - 1) / 2;
  let ways = Array(cap + 1).fill(0); ways[0] = 1;
  for (let length = 1; length <= n; length += 1) {
    let following = Array(cap + 1).fill(0), window = 0;
    for (let inversions = 0; inversions <= cap; inversions += 1) {
      window += ways[inversions];
      if (inversions >= length) window -= ways[inversions - length];
      window = (window + modulus) % modulus;
      following[inversions] = window;
    }
    if (required.has(length - 1)) {
      const wanted = required.get(length - 1), retained = following[wanted];
      following = Array(cap + 1).fill(0); following[wanted] = retained;
    }
    ways = following;
  }
  return ways.reduce((sum, value) => (sum + value) % modulus, 0);
}

const numberOfPermutations = solve;
class Solution {
  numberOfPermutations(n, requirements) { return solve(n, requirements); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfPermutations };
