'use strict';

// 1411. Number of Ways to Paint N x 3 Grid: two row-pattern classes; O(n) time and O(1) space.

function solve(n) {
  const modulus = 1000000007;
  let twoColors = 6;
  let threeColors = 6;
  for (let row = 1; row < n; row += 1) {
    [twoColors, threeColors] = [(3 * twoColors + 2 * threeColors) % modulus,
                               (2 * twoColors + 2 * threeColors) % modulus];
  }
  return (twoColors + threeColors) % modulus;
}

const numOfWays = solve;
class Solution {
  numOfWays(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numOfWays };
