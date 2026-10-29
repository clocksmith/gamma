"use strict";
// Hack2Hire 68f29e6ef567e950995157ea (Snowy Mountain Path with Melting) over an INFERRED spec; qualification unknown.

function solve(base, snow, melt) {
  const n = base.length;
  const depth = new Array(n).fill(0);
  const result = [];
  for (const fall of snow) {
    for (let i = 0; i < n; i++) {
      const v = depth[i] + fall[i] - melt;
      depth[i] = v > 0 ? v : 0;
    }
    let total = 0;
    let previous = base[0] + depth[0];
    for (let i = 1; i < n; i++) {
      const height = base[i] + depth[i];
      if (height > previous) total += height - previous;
      previous = height;
    }
    result.push(total);
  }
  return result;
}

function totalAscentByDay(base, snow, melt) { return solve(base, snow, melt); }

module.exports = solve;
module.exports.totalAscentByDay = totalAscentByDay;
