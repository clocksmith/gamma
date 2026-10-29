"use strict";
// Hack2Hire 68eabd503a3bb8f8354249a7 (Black Cell Covering Block List) over an INFERRED spec; qualification unknown.

function solve(m, n, coordinates) {
  const counts = new Map();
  for (const [x, y] of coordinates) {
    for (const a of [x - 1, x]) {
      if (a < 0 || a >= m - 1) continue;
      for (const b of [y - 1, y]) {
        if (b < 0 || b >= n - 1) continue;
        const key = a * n + b;
        counts.set(key, (counts.get(key) || 0) + 1);
      }
    }
  }
  const lists = [[], [], [], []];
  for (const key of [...counts.keys()].sort((x, y) => x - y)) lists[counts.get(key) - 1].push([Math.floor(key / n), key % n]);
  return lists;
}

function blackBlockLists(m, n, coordinates) { return solve(m, n, coordinates); }

module.exports = solve;
module.exports.blackBlockLists = blackBlockLists;
