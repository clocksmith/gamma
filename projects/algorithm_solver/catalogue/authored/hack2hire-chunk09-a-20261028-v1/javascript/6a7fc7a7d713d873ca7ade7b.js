"use strict";
// Hack2Hire 6a7fc7a7d713d873ca7ade7b (Bubble Explosion) over an INFERRED spec; qualification unknown.

function solve(bubbles) {
  const m = bubbles.length, n = bubbles[0].length;
  const g = new Array(m * n); // flat row-major copy
  for (let r = 0; r < m; r++) for (let c = 0; c < n; c++) g[r * n + c] = bubbles[r][c];
  const mark = new Uint8Array(m * n);
  for (;;) {
    mark.fill(0);
    let anyMark = false;
    for (let r = 0; r < m; r++) {
      for (let c = 0; c < n; c++) {
        const p = r * n + c, v = g[p];
        if (v === 0) continue;
        const up = r > 0 && g[p - n] === v, down = r + 1 < m && g[p + n] === v;
        const lf = c > 0 && g[p - 1] === v, rt = c + 1 < n && g[p + 1] === v;
        if (up + down + lf + rt >= 2) {
          anyMark = true; mark[p] = 1;
          if (up) mark[p - n] = 1;
          if (down) mark[p + n] = 1;
          if (lf) mark[p - 1] = 1;
          if (rt) mark[p + 1] = 1;
        }
      }
    }
    if (!anyMark) break;
    for (let c = 0; c < n; c++) {
      let write = m - 1;
      for (let r = m - 1; r >= 0; r--) {
        const p = r * n + c;
        if (g[p] && !mark[p]) { g[write * n + c] = g[p]; write -= 1; }
      }
      for (; write >= 0; write--) g[write * n + c] = 0;
    }
  }
  const out = [];
  for (let r = 0; r < m; r++) out.push(g.slice(r * n, (r + 1) * n));
  return out;
}

function explodeBubbles(bubbles) { return solve(bubbles); }

module.exports = solve;
module.exports.explodeBubbles = explodeBubbles;
