"use strict";
// Hack2Hire 684dee4b5e4cf21833c0611f (Remove Covered Point) over an INFERRED spec; qualification unknown.

function solve(intervals, idx) {
  const out = [];
  let rest = idx, done = false;
  for (const [start, end] of intervals) {
    if (!done && rest < end - start) {
      const point = start + rest;
      done = true;
      if (start < point) out.push([start, point]);
      if (point + 1 < end) out.push([point + 1, end]);
    } else {
      if (!done) rest -= end - start;
      out.push([start, end]);
    }
  }
  return out;
}

function removeCoveredPoint(intervals, idx) { return solve(intervals, idx); }

module.exports = solve;
module.exports.removeCoveredPoint = removeCoveredPoint;
