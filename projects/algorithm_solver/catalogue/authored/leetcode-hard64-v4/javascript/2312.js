'use strict';

// 2312. Selling Pieces of Wood. Rectangle DP over horizontal and vertical cuts without rotation; O(m*n*(m+n)+P) time, O(m*n) space. Inputs are preserved.

function solve(m, n, prices) {
  const best = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));
  for (const [height, width, price] of prices) best[height][width] = Math.max(best[height][width], price);
  for (let height = 1; height <= m; height += 1) {
    for (let width = 1; width <= n; width += 1) {
      for (let cut = 1; cut * 2 <= height; cut += 1) {
        best[height][width] = Math.max(best[height][width], best[cut][width] + best[height - cut][width]);
      }
      for (let cut = 1; cut * 2 <= width; cut += 1) {
        best[height][width] = Math.max(best[height][width], best[height][cut] + best[height][width - cut]);
      }
    }
  }
  return best[m][n];
}

const sellingWood = solve;
class Solution {
  sellingWood(m, n, prices) { return solve(m, n, prices); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sellingWood };
