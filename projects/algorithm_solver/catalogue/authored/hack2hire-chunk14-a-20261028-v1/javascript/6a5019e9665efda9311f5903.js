"use strict";
// Hack2Hire 6a5019e9665efda9311f5903 (Streaming Stop Token, variant 1 of 2) over an INFERRED spec; qualification unknown.

function solve(stream) {
  const out = [];
  for (const chunk of stream) {
    const position = chunk.indexOf("<END>");
    if (position >= 0) {
      if (position > 0) out.push(chunk.slice(0, position));
      return out;
    }
    out.push(chunk);
  }
  return out;
}

function truncateAtStop(stream) { return solve(stream); }

module.exports = solve;
module.exports.truncateAtStop = truncateAtStop;
