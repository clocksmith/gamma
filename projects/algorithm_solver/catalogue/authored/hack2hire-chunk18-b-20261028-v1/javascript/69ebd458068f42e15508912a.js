"use strict";
// Hack2Hire 69ebd458068f42e15508912a (Optimize Transition from Elevator to Stairs) over an INFERRED spec; qualification unknown.

function ceilDiv_(c, energy) {
  // exact integer ceiling; every product stays below 2**53
  let q = Math.floor(c / energy);
  while (q * energy < c) q += 1;
  while (q > 0 && (q - 1) * energy >= c) q -= 1;
  return q;
}

function stairs_(energy, floors, e2, c, limit) {
  // stair time from the given energy, stopping early once it reaches limit
  let total = 0;
  for (let f = 0; f < floors; f++) {
    total += ceilDiv_(c, energy);
    if (total >= limit) return total;
    energy -= e2;
  }
  return total;
}

function solve(n, e1, t1, e2, c) {
  const feasible = (k) => k === n || k * e1 - (n - k - 1) * e2 > 0;
  let lo = 0, hi = n;
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    if (feasible(mid)) hi = mid;
    else lo = mid + 1;
  }
  let best = n * t1;
  for (let k = lo; k < n; k++) {
    if (k * t1 + (n - k) >= best) break;
    const total = k * t1 + stairs_(k * e1, n - k, e2, c, best - k * t1);
    if (total < best) best = total;
  }
  return best;
}

function minimumTotalTime(n, e1, t1, e2, c) { return solve(n, e1, t1, e2, c); }

module.exports = solve;
module.exports.minimumTotalTime = minimumTotalTime;
