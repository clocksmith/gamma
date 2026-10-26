'use strict';

// 1359. Count All Valid Pickup and Delivery Options: insert each pickup/delivery pair; O(n) time and O(1) space.

function solve(n) {
  const modulus = 1000000007;
  let ways = 1;
  for (let count = 1; count <= n; count += 1) {
    // Separate reductions keep both products exact for the declared n <= 500.
    ways = ways * count % modulus;
    ways = ways * (2 * count - 1) % modulus;
  }
  return ways;
}

const countOrders = solve;
class Solution {
  countOrders(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countOrders };
