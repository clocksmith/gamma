"use strict";
// Hack2Hire 680fc04e2590daeb41a329b9 (Find Common Free Days, variant 2 of 3) over an INFERRED spec; qualification unknown.

function solve(blocks, totalDays) {
  const spans = blocks.map((b) => [b[1], b[2]]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const out = [];
  let freeFrom = 1; // first day not known to be busy
  for (const [start, end] of spans) {
    if (start > freeFrom && freeFrom <= totalDays) out.push([freeFrom, Math.min(start - 1, totalDays)]);
    freeFrom = Math.max(freeFrom, end + 1);
  }
  if (freeFrom <= totalDays) out.push([freeFrom, totalDays]);
  return out;
}

function commonFreeIntervals(blocks, totalDays) { return solve(blocks, totalDays); }

module.exports = solve;
module.exports.commonFreeIntervals = commonFreeIntervals;
