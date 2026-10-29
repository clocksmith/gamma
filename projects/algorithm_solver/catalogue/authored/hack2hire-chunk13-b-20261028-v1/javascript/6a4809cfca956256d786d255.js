"use strict";
// Hack2Hire 6a4809cfca956256d786d255 (Segment Sequence Reconstruction, variant 1 of 3) over an INFERRED spec; qualification unknown.

function solve(segments) {
  const byStart = new Map(segments.map((s) => [s[0], s]));
  const ends = new Set(segments.map((s) => s[1]));
  let segment = segments.find((s) => !ends.has(s[0]));
  const parts = [];
  while (segment !== undefined) { parts.push(segment[2]); segment = byStart.get(segment[1]); }
  return parts.join("");
}

function reconstructSequence(segments) { return solve(segments); }

module.exports = solve;
module.exports.reconstructSequence = reconstructSequence;
