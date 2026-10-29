"use strict";
// Hack2Hire 6a7cd372d713d873ca7ac6ef (Find Free Bucket ID Ranges, level 1) over an INFERRED spec; qualification unknown.

function solve(bucketRanges) {
  const spans = bucketRanges.map(([, start, end]) => [Number(start), Number(end)]).sort((p, q) => p[0] - q[0]);
  spans.push([1000, 1000]);
  const result = [];
  let cursor = 0;
  for (const [start, end] of spans) {
    if (start - cursor >= 1) result.push([String(cursor), String(start - 1)]);
    cursor = end + 1;
  }
  return result;
}

function findFreeRanges(bucketRanges) { return solve(bucketRanges); }

module.exports = solve;
module.exports.findFreeRanges = findFreeRanges;
