'use strict';

// 2787. Ways to Express an Integer as Sum of Powers: count distinct-power subsets with descending one-dimensional knapsack updates.
// O(n * floor(n^(1/x))) time and O(n) auxiliary space; inputs are read-only.
function solve(n, x) {
  const modulus = 1000000007;
  const ways = new Int32Array(n + 1);
  ways[0] = 1;
  for (let base = 1; base ** x <= n; base += 1) {
    const value = base ** x;
    for (let total = n; total >= value; total -= 1) {
      ways[total] = (ways[total] + ways[total - value]) % modulus;
    }
  }
  return ways[n];
}

const numberOfWays = solve;
class Solution {
  numberOfWays(n, x) { return solve(n, x); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfWays };
