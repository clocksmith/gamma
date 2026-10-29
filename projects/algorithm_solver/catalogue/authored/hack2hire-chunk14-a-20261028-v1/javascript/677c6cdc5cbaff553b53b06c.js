"use strict";
// Hack2Hire 677c6cdc5cbaff553b53b06c (Tail N Lines) over an INFERRED spec; qualification unknown.

function solve(text, n) {
  if (n === 0 || text.length === 0) return "";
  const ring = new Array(n).fill(0);
  let count = 0, start = 0;
  const length = text.length;
  while (start < length) {
    ring[count % n] = start;
    count += 1;
    const newline = text.indexOf("\n", start);
    if (newline < 0) break;
    start = newline + 1;
  }
  const oldest = count > n ? ring[count % n] : ring[0];
  return text.slice(oldest);
}

function tail(text, n) { return solve(text, n); }

module.exports = solve;
module.exports.tail = tail;
