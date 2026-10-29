"use strict";
// Hack2Hire 6781dbee3cd890ccd3798fc0 (Find the Nearest City) over an INFERRED spec; qualification unknown.

function solve(cities, xs, ys, queries) {
  const n = cities.length;
  const byX = Array.from({length: n}, (_, i) => i).sort((a, b) => xs[a] - xs[b] || ys[a] - ys[b]);
  const byY = Array.from({length: n}, (_, i) => i).sort((a, b) => ys[a] - ys[b] || xs[a] - xs[b]);
  const near = Array.from({length: n}, () => []);
  for (let t = 0; t + 1 < n; t++) {
    let a = byX[t], b = byX[t + 1];
    if (xs[a] === xs[b]) { near[a].push(b); near[b].push(a); }
    a = byY[t]; b = byY[t + 1];
    if (ys[a] === ys[b]) { near[a].push(b); near[b].push(a); }
  }
  const position = new Map();
  for (let i = 0; i < n; i++) position.set(cities[i], i);
  return queries.map((q) => {
    const i = position.get(q);
    let bestDistance = -1, bestName = 'NONE';
    for (const j of near[i]) {
      const d = Math.abs(xs[i] - xs[j]) + Math.abs(ys[i] - ys[j]), name = cities[j];
      if (bestDistance < 0 || d < bestDistance || (d === bestDistance && name < bestName)) { bestDistance = d; bestName = name; }
    }
    return bestName;
  });
}

function nearestCities(cities, xs, ys, queries) { return solve(cities, xs, ys, queries); }

module.exports = solve;
module.exports.nearestCities = nearestCities;
