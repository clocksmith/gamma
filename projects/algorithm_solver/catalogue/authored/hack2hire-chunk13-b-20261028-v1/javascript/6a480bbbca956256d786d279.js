"use strict";
// Hack2Hire 6a480bbbca956256d786d279 (Segment Sequence Reconstruction, variant 3 of 3) over an INFERRED spec; qualification unknown.

function solve(segments) {
  const byStart = new Map(segments.map((s) => [s[0], s]));
  const ends = new Set(segments.map((s) => s[1]));
  const heads = segments.filter((s) => !ends.has(s[0])).map((s) => s[0]).sort();
  return heads.map((head) => {
    const parts = [];
    let segment = byStart.get(head);
    while (segment !== undefined) { parts.push(segment[2]); segment = byStart.get(segment[1]); }
    return parts.join("");
  });
}

function reconstructAllSequences(segments) { return solve(segments); }

module.exports = solve;
module.exports.reconstructAllSequences = reconstructAllSequences;
