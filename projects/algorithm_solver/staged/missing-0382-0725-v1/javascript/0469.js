'use strict';

// 469. Convex Polygon. Consistent nonzero cross-product signs for the supplied simple polygon.

function solve(points) {
  let sign = 0;
  const n = points.length;
  for (let i = 0; i < n; i += 1) {
    const a = points[i], b = points[(i + 1) % n], c = points[(i + 2) % n];
    const cross = BigInt(b[0] - a[0]) * BigInt(c[1] - b[1]) - BigInt(b[1] - a[1]) * BigInt(c[0] - b[0]);
    if (cross !== 0n) {
      const current = cross > 0n ? 1 : -1;
      if (sign !== 0 && current !== sign) return false;
      sign = current;
    }
  }
  return true;
}

const isConvex = solve;
class Solution {
  isConvex(points) { return solve(points); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isConvex };
