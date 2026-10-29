"use strict";
// Hack2Hire 69a3c6546e73e4abccc9c150 (Shard Rebalancing) over an INFERRED spec; qualification unknown.

function lowerBound(a, x) { let lo = 0, hi = a.length; while (lo < hi) { const m = (lo + hi) >> 1; if (a[m] < x) lo = m + 1; else hi = m; } return lo; }
function upperBound(a, x) { let lo = 0, hi = a.length; while (lo < hi) { const m = (lo + hi) >> 1; if (a[m] <= x) lo = m + 1; else hi = m; } return lo; }
function compareShards(x, y) { return x[0] - y[0] || x[1] - y[1] || (x[2] < y[2] ? -1 : x[2] > y[2] ? 1 : 0); }

function solve(limit, shards) {
  const parsed = shards.map((shard) => { const [ident, start, end] = shard.split(":"); return [Number(start), Number(end), ident]; }).sort(compareShards);
  const starts = [], ends = [], kept = [];
  const coverage = (x) => upperBound(starts, x) - lowerBound(ends, x);
  for (const [start, end, ident] of parsed) {
    const base = lowerBound(ends, start);
    const candidate = (t) => (t === 0 ? start : ends[base + t - 1] + 1);
    let lo = 0, hi = ends.length - base;
    while (lo < hi) { // coverage is non-increasing from start, so the first point under the limit is found by bisection
      const mid = (lo + hi) >> 1;
      if (coverage(candidate(mid)) < limit) hi = mid; else lo = mid + 1;
    }
    const newStart = candidate(lo);
    if (newStart <= end) {
      starts.splice(upperBound(starts, newStart), 0, newStart);
      ends.splice(upperBound(ends, end), 0, end);
      kept.push([newStart, end, ident]);
    }
  }
  kept.sort(compareShards);
  let reach = null;
  for (const shard of kept) {
    if (reach !== null && shard[0] > reach + 1) shard[0] = reach + 1;
    reach = reach === null ? shard[1] : Math.max(reach, shard[1]);
  }
  kept.sort(compareShards);
  return kept.map(([start, end, ident]) => ident + ":" + start + ":" + end);
}

function rebalance(limit, shards) { return solve(limit, shards); }

module.exports = solve;
module.exports.rebalance = rebalance;
