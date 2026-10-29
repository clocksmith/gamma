"use strict";
// Hack2Hire 69cae7e2ff3ebde766ceda54 (Route Nearest Checkpoint) over an INFERRED spec; qualification unknown.

function solve(coordinates, distances) {
  const lengths = [], prefix = [0];
  for (let i = 0; i + 1 < coordinates.length; i++) {
    const a = coordinates[i], b = coordinates[i + 1];
    const length = Math.round(Math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2));
    lengths.push(length);
    prefix.push(prefix[prefix.length - 1] + length);
  }
  const total = prefix[prefix.length - 1];
  const out = [];
  for (const d of distances) {
    let a, b, length, r;
    if (d >= total) {
      a = b = coordinates[coordinates.length - 1]; length = 1; r = 0;
    } else {
      let lo = 0, hi = prefix.length; // last k with prefix[k] <= d
      while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (prefix[mid] <= d) lo = mid; else hi = mid; }
      a = coordinates[lo]; b = coordinates[lo + 1]; length = lengths[lo]; r = d - prefix[lo];
    }
    let best = -1, bestIndex = 0;
    coordinates.forEach((w, index) => {
      const dx = length * (a[0] - w[0]) + r * (b[0] - a[0]);
      const dy = length * (a[1] - w[1]) + r * (b[1] - a[1]);
      const q = dx * dx + dy * dy;
      if (best < 0 || q < best) { best = q; bestIndex = index; }
    });
    out.push(bestIndex);
  }
  return out;
}

function nearestCheckpoints(coordinates, distances) { return solve(coordinates, distances); }

module.exports = solve;
module.exports.nearestCheckpoints = nearestCheckpoints;
