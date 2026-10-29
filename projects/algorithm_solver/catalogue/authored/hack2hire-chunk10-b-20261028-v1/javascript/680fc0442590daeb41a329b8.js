"use strict";
// Hack2Hire 680fc0442590daeb41a329b8 (Find Common Free Days, variant 1 of 3) over an INFERRED spec; qualification unknown.

function solve(blocks, totalDays) {
  const diff = new Array(totalDays + 2).fill(0);
  for (const [, start, end] of blocks) {
    if (start <= totalDays) { diff[start] += 1; diff[Math.min(end, totalDays) + 1] -= 1; }
  }
  const out = [];
  let covered = 0;
  for (let day = 1; day <= totalDays; day++) {
    covered += diff[day];
    if (covered === 0) out.push(day);
  }
  return out;
}

function commonFreeDays(blocks, totalDays) { return solve(blocks, totalDays); }

module.exports = solve;
module.exports.commonFreeDays = commonFreeDays;
