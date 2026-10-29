"use strict";
// Hack2Hire 69bef92321f6ab4226963c6b (Linear Interpolation) over an INFERRED spec; qualification unknown.

function gcd(a, b) { while (b) { const t = a % b; a = b; b = t; } return a; }

function ratio(num, den) {
  if (num === 0) return "0";
  const g = gcd(Math.abs(num), den);
  num /= g; den /= g;
  return den === 1 ? String(num) : String(num) + "/" + String(den);
}

function solve(points, queries) {
  const high = new Map(), low = new Map();
  for (const [x, y] of points) {
    if (!high.has(x) || y > high.get(x)) high.set(x, y);
    if (!low.has(x) || y < low.get(x)) low.set(x, y);
  }
  const xs = [...high.keys()].sort((a, b) => a - b);
  const out = [];
  for (const q of queries) {
    let lo = 0, hi = xs.length;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (xs[mid] < q) lo = mid + 1; else hi = mid; }
    if (lo < xs.length && xs[lo] === q) out.push(String(high.get(q)));
    else if (lo === 0) out.push(String(low.get(xs[0])));
    else if (lo === xs.length) out.push(String(high.get(xs[xs.length - 1])));
    else {
      const x1 = xs[lo - 1], x2 = xs[lo], y1 = high.get(x1), y2 = low.get(x2);
      out.push(ratio(y1 * (x2 - x1) + (y2 - y1) * (q - x1), x2 - x1));
    }
  }
  return out;
}

function interpolate(points, queries) { return solve(points, queries); }

module.exports = solve;
module.exports.interpolate = interpolate;
