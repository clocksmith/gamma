"use strict";
// Hack2Hire 69279ce99c0536c47b291a80 (Find Peak Event Moment) over an INFERRED spec; qualification unknown.

function solve(intervals) {
  const starts = intervals.map((iv) => iv[0]).sort((a, b) => a - b);
  const ends = intervals.map((iv) => iv[1]).sort((a, b) => a - b);
  let present = 0;
  let best = 0;
  let moment = starts[0];
  let j = 0;
  for (const s of starts) {
    while (ends[j] <= s) { present--; j++; }
    present++;
    if (present > best) { best = present; moment = s; }
  }
  return moment;
}

function findPeakMoment(intervals) { return solve(intervals); }

module.exports = solve;
module.exports.findPeakMoment = findPeakMoment;
