"use strict";
// Hack2Hire 6a21d6fcd5c5b3e5f9c345f1 (Count Singler Role Co-occurrences) over an INFERRED spec; qualification unknown.

function solve(performances, period) {
  const bySinger = new Map();
  for (const [singer, role, year] of performances) {
    if (!bySinger.has(singer)) bySinger.set(singer, new Map());
    const roles = bySinger.get(singer);
    if (!roles.has(role)) roles.set(role, new Set());
    roles.get(role).add(Number(year));
  }
  const cmp = (x, y) => (x < y ? -1 : x > y ? 1 : 0);
  const counts = new Map();  // role -> Map(otherRole -> count)
  const bump = (x, y) => {
    if (!counts.has(x)) counts.set(x, new Map());
    const row = counts.get(x);
    row.set(y, (row.get(y) || 0) + 1);
  };
  for (const roles of bySinger.values()) {
    const names = [...roles.keys()].sort(cmp);
    const years = names.map((name) => [...roles.get(name)].sort((x, y) => x - y));
    for (let x = 0; x < names.length; x++) {
      const xs = years[x];
      for (let y = x + 1; y < names.length; y++) {
        const ys = years[y];
        let i = 0, j = 0;
        while (i < xs.length && j < ys.length) {
          if (Math.abs(xs[i] - ys[j]) <= period) { bump(names[x], names[y]); bump(names[y], names[x]); break; }
          if (xs[i] < ys[j]) i++; else j++;
        }
      }
    }
  }
  const out = [];
  for (const a of [...counts.keys()].sort(cmp)) {
    const row = counts.get(a);
    for (const b of [...row.keys()].sort(cmp)) out.push([a, b, String(row.get(b))]);
  }
  return out;
}

function roleCooccurrences(performances, period) { return solve(performances, period); }

module.exports = solve;
module.exports.roleCooccurrences = roleCooccurrences;
