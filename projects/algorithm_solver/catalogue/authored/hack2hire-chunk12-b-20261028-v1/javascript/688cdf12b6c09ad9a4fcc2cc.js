"use strict";
// Hack2Hire 688cdf12b6c09ad9a4fcc2cc (Minimum Distance to All Points) over an INFERRED spec; qualification unknown.

function solve(nums) {
  const ordered = Float64Array.from(nums).sort();
  const x = ordered[(ordered.length - 1) >> 1];
  let total = 0;
  for (const v of nums) total += Math.abs(v - x);
  return [x, total];
}

function minTotalDistance(nums) { return solve(nums); }

module.exports = solve;
module.exports.minTotalDistance = minTotalDistance;
