"use strict";
// Hack2Hire 69752cb217272b5c868d5e84 (Schedule Orders onto Planes) over an INFERRED spec; qualification unknown.

function solve(planes, orders) {
  const fleet = planes.map((p) => [p[0], p[1]]).sort((x, y) => x[0] - y[0]);
  const departures = fleet.map((p) => p[0]);
  let size = 1;
  while (size < fleet.length) size *= 2;
  const tree = new Array(2 * size).fill(-1);
  fleet.forEach((p, i) => { tree[size + i] = p[1]; });
  for (let node = size - 1; node > 0; node--) tree[node] = Math.max(tree[2 * node], tree[2 * node + 1]);
  const update = (i, value) => {
    let node = size + i;
    tree[node] = value;
    for (node >>= 1; node; node >>= 1) tree[node] = Math.max(tree[2 * node], tree[2 * node + 1]);
  };
  const first = (node, lo, hi, start, need) => {
    // leftmost leaf index >= start in [lo, hi) holding at least need, or -1
    if (hi <= start || tree[node] < need) return -1;
    if (hi - lo === 1) return lo;
    const mid = (lo + hi) >> 1;
    const found = first(2 * node, lo, mid, start, need);
    return found !== -1 ? found : first(2 * node + 1, mid, hi, start, need);
  };
  const out = [];
  for (const [shipTime, items] of orders) {
    let lo = 0, hi = departures.length; // first departure strictly after shipTime
    while (lo < hi) { const mid = (lo + hi) >> 1; if (departures[mid] <= shipTime) lo = mid + 1; else hi = mid; }
    const log = [];
    let chosen = [];
    for (const item of items) {
      const i = first(1, 0, size, lo, item);
      if (i === -1) {
        for (let k = log.length - 1; k >= 0; k--) update(log[k][0], log[k][1]);
        chosen = [];
        break;
      }
      log.push([i, tree[size + i]]);
      update(i, tree[size + i] - item);
      chosen.push(departures[i]);
    }
    out.push(chosen);
  }
  return out;
}

function scheduleOrders(planes, orders) { return solve(planes, orders); }

module.exports = solve;
module.exports.scheduleOrders = scheduleOrders;
