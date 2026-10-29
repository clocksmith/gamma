"use strict";
// Hack2Hire 69b62ed7666464810ca36212 (Largest Rectangle Area, variant 2 of 2) over an INFERRED spec; qualification unknown.

function solve(points) {
  const groups = new Map(); // "x sum,y sum,squared length" -> point index pairs: diagonals sharing midpoint and length
  const n = points.length;
  for (let i = 0; i < n; i++) {
    const [px, py] = points[i];
    for (let j = i + 1; j < n; j++) {
      const [qx, qy] = points[j], dx = qx - px, dy = qy - py;
      const key = (px + qx) + "," + (py + qy) + "," + (dx * dx + dy * dy);
      let list = groups.get(key);
      if (list === undefined) { list = []; groups.set(key, list); }
      list.push(i, j);
    }
  }
  let best = 0;
  for (const pairs of groups.values()) {
    for (let a = 0; a < pairs.length; a += 2) {
      const p = points[pairs[a]];
      for (let b = a + 2; b < pairs.length; b += 2) {
        const u = points[pairs[b]], v = points[pairs[b + 1]];
        const area = Math.abs((u[0] - p[0]) * (v[1] - p[1]) - (u[1] - p[1]) * (v[0] - p[0]));
        if (area > best) best = area;
      }
    }
  }
  return best;
}

function largestRectangleArea(points) { return solve(points); }

module.exports = solve;
module.exports.largestRectangleArea = largestRectangleArea;
