"use strict";
// Hack2Hire 6a480ba0ca956256d786d277 (Segment Sequence Reconstruction, variant 2 of 3) over an INFERRED spec; qualification unknown.

function solve(segments) {
  const byStart = new Map(segments.map((s) => [s[0], s]));
  const ends = new Set(segments.map((s) => s[1]));
  const heads = segments.filter((s) => !ends.has(s[0]));
  if (heads.length !== 1) return "";
  const parts = [];
  let segment = heads[0];
  while (segment !== undefined) { parts.push(segment[2]); segment = byStart.get(segment[1]); }
  return parts.length === segments.length ? parts.join("") : "";
}

function reconstructSequence(segments) { return solve(segments); }

module.exports = solve;
module.exports.reconstructSequence = reconstructSequence;
