"use strict";
// Hack2Hire 690425df4845d25b8e994896 (Closest Pair of Points) over an INFERRED spec; qualification unknown.

function solve(points) {
  const pts = points.map((p) => [p[0], p[1]]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  let best = (pts[0][0] - pts[1][0]) ** 2 + (pts[0][1] - pts[1][1]) ** 2;

  function rec(lo, hi) {
    if (hi - lo <= 3) {
      const part = pts.slice(lo, hi);
      for (let i = 0; i < part.length; i++) {
        for (let j = i + 1; j < part.length; j++) {
          const d = (part[i][0] - part[j][0]) ** 2 + (part[i][1] - part[j][1]) ** 2;
          if (d < best) best = d;
        }
      }
      return part.sort((a, b) => a[1] - b[1]);
    }
    const mid = (lo + hi) >> 1, midX = pts[mid][0];
    const left = rec(lo, mid), right = rec(mid, hi);
    const merged = [];
    let i = 0, j = 0;
    while (i < left.length && j < right.length) {
      if (left[i][1] <= right[j][1]) merged.push(left[i++]); else merged.push(right[j++]);
    }
    while (i < left.length) merged.push(left[i++]);
    while (j < right.length) merged.push(right[j++]);
    const strip = merged.filter((q) => (q[0] - midX) ** 2 < best);
    for (let a = 0; a < strip.length; a++) {
      for (let b = a + 1; b < strip.length; b++) {
        const dy = strip[b][1] - strip[a][1];
        if (dy * dy >= best) break;
        const d = (strip[b][0] - strip[a][0]) ** 2 + dy * dy;
        if (d < best) best = d;
      }
    }
    return merged;
  }

  rec(0, pts.length);
  return Math.sqrt(best);
}

function closestPair(points) { return solve(points); }

module.exports = solve;
module.exports.closestPair = closestPair;
