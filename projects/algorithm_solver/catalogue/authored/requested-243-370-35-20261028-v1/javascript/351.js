"use strict";

function solve(m, n) {
  const skip = Array.from({ length: 10 }, () => new Int32Array(10));
  skip[1][3] = skip[3][1] = 2;
  skip[1][7] = skip[7][1] = 4;
  skip[3][9] = skip[9][3] = 6;
  skip[7][9] = skip[9][7] = 8;
  skip[1][9] = skip[9][1] = skip[2][8] = skip[8][2] = skip[3][7] = skip[7][3] = skip[4][6] = skip[6][4] = 5;

  function dfs(vis, cur, rem) {
    if (rem === 0) return 1;
    const nvis = vis | (1 << cur);
    let total = 0;
    for (let nxt = 1; nxt <= 9; nxt++) {
      const mid = skip[cur][nxt];
      if (((nvis >> nxt) & 1) === 0 && (mid === 0 || ((nvis >> mid) & 1) !== 0)) {
        total += dfs(nvis, nxt, rem - 1);
      }
    }
    return total;
  }

  let ans = 0;
  for (let len = m; len <= n; len++) {
    ans += dfs(0, 1, len - 1) * 4;
    ans += dfs(0, 2, len - 1) * 4;
    ans += dfs(0, 5, len - 1);
  }
  return ans;
}

function numberOfPatterns(m, n) {
  return solve(m, n);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.numberOfPatterns = numberOfPatterns;
