"use strict";
// Hack2Hire 69a4fb4e3d95612a1782bbd2 (Largest Rectangle Area, variant 1 of 2) over an INFERRED spec; qualification unknown.

function solve(points) {
  const ordered = points.map((p) => [p[0], p[1]]).sort((p, q) => p[0] - q[0] || p[1] - q[1]);
  const firstColumn = new Map(); // (y1, y2) packed as y1 * 40001 + y2 -> smallest x holding both
  let best = 0, i = 0;
  while (i < ordered.length) {
    const x = ordered[i][0];
    let j = i;
    while (j < ordered.length && ordered[j][0] === x) j++;
    const ys = ordered.slice(i, j).map((p) => p[1]);
    for (let a = 0; a < ys.length; a++) {
      for (let b = a + 1; b < ys.length; b++) {
        const key = ys[a] * 40001 + ys[b], seen = firstColumn.get(key);
        if (seen === undefined) firstColumn.set(key, x);
        else { const area = (x - seen) * (ys[b] - ys[a]); if (area > best) best = area; }
      }
    }
    i = j;
  }
  return best;
}

function largestRectangleArea(points) { return solve(points); }

module.exports = solve;
module.exports.largestRectangleArea = largestRectangleArea;
