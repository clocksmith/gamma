"use strict";
// Hack2Hire 6a7cd38bd713d873ca7ac6f0 (Find Free Bucket ID Ranges, level 2) over an INFERRED spec; qualification unknown.

function solve(bucketRanges, minSize) {
  const spans = bucketRanges.map(([, start, end]) => [Number(start), Number(end)]).sort((p, q) => p[0] - q[0]);
  spans.push([1000, 1000]);
  const result = [];
  let cursor = 0;
  for (const [start, end] of spans) {
    if (start - cursor >= Math.max(1, minSize)) result.push([String(cursor), String(start - 1)]);
    cursor = end + 1;
  }
  return result;
}

function findFreeRanges(bucketRanges, minSize) { return solve(bucketRanges, minSize); }

module.exports = solve;
module.exports.findFreeRanges = findFreeRanges;
