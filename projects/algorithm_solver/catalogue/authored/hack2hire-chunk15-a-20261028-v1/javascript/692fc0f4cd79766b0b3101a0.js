"use strict";
// Hack2Hire 692fc0f4cd79766b0b3101a0 (Count Intervals Covering Point) over an INFERRED spec; qualification unknown.

function upperBound(a, x) {
  let lo = 0, hi = a.length;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (a[mid] <= x) lo = mid + 1; else hi = mid; }
  return lo;
}

function lowerBound(a, x) {
  let lo = 0, hi = a.length;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (a[mid] < x) lo = mid + 1; else hi = mid; }
  return lo;
}

class IntervalCounter {
  constructor(intervals) {
    this.starts = Float64Array.from(intervals, (iv) => iv[0]).sort();
    this.ends = Float64Array.from(intervals, (iv) => iv[1]).sort();
  }

  count(x) {
    return upperBound(this.starts, x) - lowerBound(this.ends, x);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "IntervalCounter" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new IntervalCounter(...argumentLists[0]);
  const allowed = new Set(["count"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.IntervalCounter = IntervalCounter;
