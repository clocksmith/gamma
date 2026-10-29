"use strict";
// Hack2Hire 68e9a2a2149617c9114ece06 (Minimize a Convex Function) over an INFERRED spec; qualification unknown.

function solve(lines, a, b, eps) {
  const value = (x) => {
    let best = -Infinity;
    for (let i = 0; i < lines.length; i++) {
      const v = lines[i][0] * x + lines[i][1];
      if (v > best) best = v;
    }
    return best;
  };
  let lo = 0, hi = (b - a - (b - a) % eps) / eps;
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    if (value(a + mid * eps) <= value(a + (mid + 1) * eps)) hi = mid;
    else lo = mid + 1;
  }
  return a + lo * eps;
}

function minimizeConvex(lines, a, b, eps) { return solve(lines, a, b, eps); }

module.exports = solve;
module.exports.minimizeConvex = minimizeConvex;
