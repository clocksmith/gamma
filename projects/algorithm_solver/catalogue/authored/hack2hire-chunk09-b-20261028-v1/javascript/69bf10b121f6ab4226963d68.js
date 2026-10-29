"use strict";
// Hack2Hire 69bf10b121f6ab4226963d68 (Chunk a List of Lists) over an INFERRED spec; qualification unknown.

function solve(data, size) {
  const out = [];
  let buffer = [];
  for (const inner of data) {
    for (const value of inner) {
      buffer.push(value);
      if (buffer.length === size) { out.push(buffer); buffer = []; }
    }
  }
  if (buffer.length) out.push(buffer);
  return out;
}

function rechunk(data, size) { return solve(data, size); }

module.exports = solve;
module.exports.rechunk = rechunk;
