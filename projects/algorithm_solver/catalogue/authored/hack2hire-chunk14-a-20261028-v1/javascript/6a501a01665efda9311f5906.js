"use strict";
// Hack2Hire 6a501a01665efda9311f5906 (Streaming Stop Token, variant 2 of 2) over an INFERRED spec; qualification unknown.

function solve(stream) {
  const position = stream.join("").indexOf("<END>");
  if (position < 0) return stream.slice();
  const out = [];
  let start = 0;
  for (const chunk of stream) {
    if (start <= position && position < start + chunk.length) {
      if (position > start) out.push(chunk.slice(0, position - start));
      return out;
    }
    out.push(chunk);
    start += chunk.length;
  }
  return out;
}

function truncateAtSplitStop(stream) { return solve(stream); }

module.exports = solve;
module.exports.truncateAtSplitStop = truncateAtSplitStop;
