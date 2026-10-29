"use strict";
// Hack2Hire 67eb157b4c9bb801bfd0ef6f (Offset Commit) over an INFERRED spec; qualification unknown.

function solve(offsets) {
  const done = new Set();
  let next = 0;
  const out = new Array(offsets.length);
  for (let i = 0; i < offsets.length; i++) {
    done.add(offsets[i]);
    const start = next;
    while (done.has(next)) { done.delete(next); next++; }
    out[i] = next > start ? next - 1 : -1;
  }
  return out;
}

function commitOffsets(offsets) { return solve(offsets); }

module.exports = solve;
module.exports.commitOffsets = commitOffsets;
