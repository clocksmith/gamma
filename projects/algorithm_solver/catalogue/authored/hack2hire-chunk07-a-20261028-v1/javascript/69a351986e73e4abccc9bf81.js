"use strict";
// Hack2Hire 69a351986e73e4abccc9bf81 (Longest Consecutive Segment After Insertions) over an INFERRED spec; qualification unknown.

function solve(queries) {
  const occupied = new Set(), length = new Map(), out = [];
  let best = 0;
  for (const p of queries) {
    if (!occupied.has(p) && !(occupied.has(p - 1) && occupied.has(p + 1))) {
      occupied.add(p);
      const left = occupied.has(p - 1) ? length.get(p - 1) : 0;
      const right = occupied.has(p + 1) ? length.get(p + 1) : 0;
      const total = left + right + 1;
      length.set(p - left, total);
      length.set(p + right, total);
      if (total > best) best = total;
    }
    out.push(best);
  }
  return out;
}

function longestSegments(queries) { return solve(queries); }

module.exports = solve;
module.exports.longestSegments = longestSegments;
