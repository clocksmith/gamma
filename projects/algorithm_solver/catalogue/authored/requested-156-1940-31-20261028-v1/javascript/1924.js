"use strict";

function dist(a, b) {
  return Math.hypot(a[0] - b[0], a[1] - b[1]);
}

function circle2(a, b) {
  return [(a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0, dist(a, b) / 2.0];
}

function circle3(a, b, c) {
  const [ax, ay] = a, [bx, by] = b, [cx, cy] = c;
  const d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by));
  if (Math.abs(d) < 1e-12) {
    const pairs = [circle2(a, b), circle2(b, c), circle2(a, c)];
    pairs.sort((x, y) => y[2] - x[2]);
    return pairs[0];
  }
  const a2 = ax * ax + ay * ay;
  const b2 = bx * bx + by * by;
  const c2 = cx * cx + cy * cy;
  const ux = (a2 * (by - cy) + b2 * (cy - ay) + c2 * (ay - by)) / d;
  const uy = (a2 * (cx - bx) + b2 * (ax - cx) + c2 * (bx - ax)) / d;
  return [ux, uy, Math.hypot(ux - ax, uy - ay)];
}

function solve(trees) {
  const seen = new Set();
  const pts = [];
  for (let i = 0; i < trees.length; i++) {
    const key = `${trees[i][0]},${trees[i][1]}`;
    if (!seen.has(key)) {
      seen.add(key);
      pts.push([trees[i][0], trees[i][1]]);
    }
  }
  let c = [pts[0][0], pts[0][1], 0.0];
  for (let i = 0; i < pts.length; i++) {
    if (dist([c[0], c[1]], pts[i]) > c[2] + 1e-9) {
      c = [pts[i][0], pts[i][1], 0.0];
      for (let j = 0; j < i; j++) {
        if (dist([c[0], c[1]], pts[j]) > c[2] + 1e-9) {
          c = circle2(pts[i], pts[j]);
          for (let k = 0; k < j; k++) {
            if (dist([c[0], c[1]], pts[k]) > c[2] + 1e-9) {
              c = circle3(pts[i], pts[j], pts[k]);
            }
          }
        }
      }
    }
  }
  return [
    Math.round(c[0] * 1e5) / 1e5,
    Math.round(c[1] * 1e5) / 1e5,
    Math.round(c[2] * 1e5) / 1e5,
  ];
}

function outerTrees(trees) {
  return solve(trees);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.outerTrees = outerTrees;
