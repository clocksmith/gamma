"use strict";
// Hack2Hire 67e4468750b60b77022f381c (Maximum Multiplier Path) over an INFERRED spec; qualification unknown.

function solve(n, edges, start, end) {
  const out = Array.from({length: n}, () => []);
  for (const [u, v, w] of edges) out[u].push([v, w]);
  const best = Array.from({length: 1 << n}, () => new Array(n).fill(-1)); // best[mask][v]: largest product of a simple path start..v visiting mask
  best[1 << start][start] = 1;
  let answer = -1;
  for (let mask = 0; mask < 1 << n; mask++) {
    if (!(mask >> start & 1)) continue;
    const row = best[mask];
    for (let v = 0; v < n; v++) {
      const p = row[v];
      if (p < 0) continue;
      if (v === end && p > answer) answer = p;
      for (const [w, mult] of out[v]) {
        if (!(mask >> w & 1)) { const nxt = best[mask | 1 << w]; if (p * mult > nxt[w]) nxt[w] = p * mult; }
      }
    }
  }
  return answer;
}

function maxMultiplierProduct(n, edges, start, end) { return solve(n, edges, start, end); }

module.exports = solve;
module.exports.maxMultiplierProduct = maxMultiplierProduct;
