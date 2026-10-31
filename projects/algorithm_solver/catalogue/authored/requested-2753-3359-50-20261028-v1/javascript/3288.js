"use strict";

function lis2d(pts) {
  pts.sort((a, b) => (a[0] !== b[0] ? a[0] - b[0] : b[1] - a[1]));
  const tails = [];
  for (let i = 0; i < pts.length; i++) {
    const y = pts[i][1];
    let lo = 0, hi = tails.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (tails[mid] < y) lo = mid + 1;
      else hi = mid;
    }
    if (lo === tails.length) tails.push(y);
    else tails[lo] = y;
  }
  return tails.length;
}

function solve(coordinates, k) {
  const [xk, yk] = coordinates[k];
  const left = [];
  const right = [];
  for (let i = 0; i < coordinates.length; i++) {
    const [x, y] = coordinates[i];
    if (x < xk && y < yk) left.push([x, y]);
    else if (x > xk && y > yk) right.push([x, y]);
  }
  return 1 + lis2d(left) + lis2d(right);
}

function maxPathLength(coordinates, k) {
  return solve(coordinates, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.maxPathLength = maxPathLength;
