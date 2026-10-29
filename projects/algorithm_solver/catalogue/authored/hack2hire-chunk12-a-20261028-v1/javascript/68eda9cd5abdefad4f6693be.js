"use strict";
// Hack2Hire 68eda9cd5abdefad4f6693be (Maximum Interval Overlap Count) over an INFERRED spec; qualification unknown.

function solve(intervals) {
  const starts = intervals.map((iv) => iv[0]).sort((a, b) => a - b);
  const ends = intervals.map((iv) => iv[1]).sort((a, b) => a - b);
  let i = 0, j = 0, current = 0, best = 0;
  while (i < starts.length) {
    if (starts[i] <= ends[j]) { current++; i++; if (current > best) best = current; } // closed: start at an end still overlaps
    else { current--; j++; }
  }
  return best;
}

function maxOverlap(intervals) { return solve(intervals); }

module.exports = solve;
module.exports.maxOverlap = maxOverlap;
