"use strict";

function solve(heights, volume, k) {
  const h = heights.slice();
  const n = h.length;
  for (let v = 0; v < volume; v++) {
    let pos = k;
    for (let i = k - 1; i >= 0; i--) {
      if (h[i] > h[pos]) break;
      if (h[i] < h[pos]) pos = i;
    }
    if (pos === k) {
      for (let i = k + 1; i < n; i++) {
        if (h[i] > h[pos]) break;
        if (h[i] < h[pos]) pos = i;
      }
    }
    h[pos]++;
  }
  return h;
}

function pourWater(heights, volume, k) {
  return solve(heights, volume, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.pourWater = pourWater;
