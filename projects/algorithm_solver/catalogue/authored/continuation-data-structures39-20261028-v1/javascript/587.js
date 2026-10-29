"use strict";

function cross(o, a, b) {
  return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
}

function solve(trees) {
  const pts = trees.map((p) => [p[0], p[1]]).sort((a, b) => (a[0] !== b[0] ? a[0] - b[0] : a[1] - b[1]));
  if (pts.length <= 3) return pts;
  const lower = [];
  for (let i = 0; i < pts.length; i++) {
    const p = pts[i];
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) < 0) {
      lower.pop();
    }
    lower.push(p);
  }
  const upper = [];
  for (let i = pts.length - 1; i >= 0; i--) {
    const p = pts[i];
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) < 0) {
      upper.pop();
    }
    upper.push(p);
  }
  const seen = new Set();
  const hull = [];
  for (const p of lower.concat(upper)) {
    const k = p[0] + "," + p[1];
    if (!seen.has(k)) {
      seen.add(k);
      hull.push(p);
    }
  }
  hull.sort((a, b) => (a[0] !== b[0] ? a[0] - b[0] : a[1] - b[1]));
  return hull;
}

function outerTrees(trees) {
  return solve(trees);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.outerTrees = outerTrees;
