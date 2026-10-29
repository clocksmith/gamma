"use strict";

function solve(points) {
  const pts = new Set();
  let minX = Infinity, maxX = -Infinity;
  for (let i = 0; i < points.length; i++) {
    const [x, y] = points[i];
    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
    pts.add(`${x},${y}`);
  }
  const sumX = minX + maxX;
  for (let i = 0; i < points.length; i++) {
    const [x, y] = points[i];
    if (!pts.has(`${sumX - x},${y}`)) return false;
  }
  return true;
}

function isReflected(points) {
  return solve(points);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.isReflected = isReflected;
