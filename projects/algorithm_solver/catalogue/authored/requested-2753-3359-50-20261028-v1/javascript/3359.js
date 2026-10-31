"use strict";

function solve(grid, k) {
  const m = grid.length, n = grid[0].length;
  const width = Array.from({ length: m }, () => new Int32Array(n));
  for (let r = 0; r < m; r++) {
    for (let c = 0; c < n; c++) {
      if (grid[r][c] <= k) {
        if (c > 0 && grid[r][c - 1] <= k && grid[r][c - 1] >= grid[r][c]) {
          width[r][c] = width[r][c - 1] + 1;
        } else {
          width[r][c] = 1;
        }
      }
    }
  }
  let total = 0;
  for (let c = 0; c < n; c++) {
    const stackW = [];
    const stackC = [];
    let colSum = 0;
    for (let r = 0; r < m; r++) {
      const w = width[r][c];
      let cnt = 1;
      while (stackW.length > 0 && stackW[stackW.length - 1] >= w) {
        const pw = stackW.pop();
        const pcnt = stackC.pop();
        colSum -= pw * pcnt;
        cnt += pcnt;
      }
      stackW.push(w);
      stackC.push(cnt);
      colSum += w * cnt;
      total += colSum;
    }
  }
  return total;
}

function countSubmatrices(grid, k) {
  return solve(grid, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.countSubmatrices = countSubmatrices;
