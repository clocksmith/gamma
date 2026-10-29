"use strict";
// Hack2Hire 67ff11d2a19f45c95d40567f (Three-Color Map Coloring) over an INFERRED spec; qualification unknown.

function solve(locations, adjacencies) {
  const n = locations.length, index = new Map(locations.map((name, i) => [name, i]));
  const sets = Array.from({length: n}, () => new Set());
  for (const [a, b] of adjacencies) { sets[index.get(a)].add(index.get(b)); sets[index.get(b)].add(index.get(a)); }
  const neighbours = sets.map((s) => [...s].sort((x, y) => x - y));
  const colour = new Array(n).fill(-1), seen = Array.from({length: n}, () => [0, 0, 0]);
  function pick() {
    let best = -1, sat = -1, deg = -1;
    for (let v = 0; v < n; v++) {
      if (colour[v] >= 0) continue;
      const s = (seen[v][0] > 0) + (seen[v][1] > 0) + (seen[v][2] > 0), d = neighbours[v].length;
      if (s > sat || (s === sat && d > deg)) { best = v; sat = s; deg = d; }
    }
    return [best, sat];
  }
  function search(left) {
    if (left === 0) return true;
    const [v, sat] = pick();
    const options = sat === 0 ? [0] : [0, 1, 2];
    for (const c of options) {
      if (seen[v][c]) continue;
      colour[v] = c;
      for (const u of neighbours[v]) seen[u][c]++;
      if (search(left - 1)) return true;
      for (const u of neighbours[v]) seen[u][c]--;
      colour[v] = -1;
    }
    return false;
  }
  return search(n);
}

function canThreeColor(locations, adjacencies) { return solve(locations, adjacencies); }

module.exports = solve;
module.exports.canThreeColor = canThreeColor;
