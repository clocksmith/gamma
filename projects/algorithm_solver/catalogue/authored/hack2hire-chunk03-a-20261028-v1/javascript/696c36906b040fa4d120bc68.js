"use strict";
// Hack2Hire 696c36906b040fa4d120bc68 (Linear Interpolation of Missing Points) over an INFERRED spec; qualification unknown.

function gcd(a, b) { while (b) { const t = a % b; a = b; b = t; } return a; }

function ratio(num, den) {
  if (num === 0) return "0";
  const g = gcd(Math.abs(num), den);
  num /= g; den /= g;
  return den === 1 ? String(num) : String(num) + "/" + String(den);
}

function solve(interval, points) {
  const out = [[points[0][0], String(points[0][1])]];
  for (let i = 1; i < points.length; i++) {
    const [x1, y1] = points[i - 1], [x2, y2] = points[i];
    const gap = x2 - x1;
    if (gap > interval) {
      for (let x = x1 + interval; x < x2; x += interval) out.push([x, ratio(y1 * gap + (y2 - y1) * (x - x1), gap)]);
    }
    out.push([x2, String(y2)]);
  }
  return out;
}

function fillMissingPoints(interval, points) { return solve(interval, points); }

module.exports = solve;
module.exports.fillMissingPoints = fillMissingPoints;
