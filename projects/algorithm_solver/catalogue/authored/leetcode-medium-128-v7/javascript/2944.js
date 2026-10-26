'use strict';

// 2944. Minimum Number of Coins for Fruits: choose the next paid fruit anywhere within or immediately beyond the current free range.
// O(n * n) time and O(n) auxiliary space; inputs are read-only.
function solve(prices) {
  const size = prices.length;
  const best = new Array(size + 1).fill(0);
  for (let index = size - 1; index >= 0; index -= 1) {
    let following = Infinity;
    for (let next = index + 1; next <= Math.min(size, 2 * index + 2); next += 1) {
      following = Math.min(following, best[next]);
    }
    best[index] = prices[index] + following;
  }
  return best[0];
}

const minimumCoins = solve;
class Solution {
  minimumCoins(prices) { return solve(prices); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumCoins };
