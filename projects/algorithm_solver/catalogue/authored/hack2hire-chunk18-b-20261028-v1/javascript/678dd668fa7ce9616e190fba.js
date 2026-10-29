"use strict";
// Hack2Hire 678dd668fa7ce9616e190fba (Sum of Islands Max) over an INFERRED spec; qualification unknown.

function solve(grid) {
  const m = grid.length, n = grid[0].length;
  const seen = [];
  for (let i = 0; i < m; i++) seen.push(new Array(n).fill(false));
  let best = 0;
  for (let si = 0; si < m; si++) {
    for (let sj = 0; sj < n; sj++) {
      if (grid[si][sj] <= 0 || seen[si][sj]) continue;
      seen[si][sj] = true;
      const stack = [si * n + sj];
      let total = 0;
      while (stack.length) {
        const cell = stack.pop();
        const i = Math.floor(cell / n), j = cell - i * n;
        total += grid[i][j];
        for (const [a, b] of [[i - 1, j], [i + 1, j], [i, j - 1], [i, j + 1]]) {
          if (a >= 0 && a < m && b >= 0 && b < n && !seen[a][b] && grid[a][b] > 0) {
            seen[a][b] = true;
            stack.push(a * n + b);
          }
        }
      }
      if (total > best) best = total;
    }
  }
  return best;
}

function maxIslandSum(grid) { return solve(grid); }

module.exports = solve;
module.exports.maxIslandSum = maxIslandSum;
