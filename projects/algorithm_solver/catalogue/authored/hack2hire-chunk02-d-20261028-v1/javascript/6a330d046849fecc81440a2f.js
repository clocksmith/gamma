"use strict";
// Hack2Hire 6a330d046849fecc81440a2f (Diagonal Server Redirects) over an INFERRED spec; qualification unknown.

function lowerBound(values, x) {
  let lo = 0, hi = values.length;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (values[mid] < x) lo = mid + 1; else hi = mid; }
  return lo;
}

function solve(locations, redirectRecords) {
  const main = new Map(), anti = new Map();
  for (const [x, y] of locations) {
    if (!main.has(x - y)) main.set(x - y, []);
    main.get(x - y).push(x);
    if (!anti.has(x + y)) anti.set(x + y, []);
    anti.get(x + y).push(x);
  }
  for (const xs of main.values()) xs.sort((p, q) => p - q);
  for (const xs of anti.values()) xs.sort((p, q) => p - q);
  let [a, b] = locations[0];
  for (const d of redirectRecords) {
    const onMain = d === 1 || d === 4;
    const key = onMain ? a - b : a + b;
    const xs = onMain ? main.get(key) : anti.get(key);
    let nx;
    if (d === 1 || d === 2) {
      const i = lowerBound(xs, a + 1);
      if (i === xs.length) continue;
      nx = xs[i];
    } else {
      const i = lowerBound(xs, a);
      if (i === 0) continue;
      nx = xs[i - 1];
    }
    a = nx;
    b = onMain ? nx - key : key - nx;
  }
  return [a, b];
}

function findFinalServer(locations, redirectRecords) { return solve(locations, redirectRecords); }

module.exports = solve;
module.exports.findFinalServer = findFinalServer;
