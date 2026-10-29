"use strict";
// Hack2Hire 69c2f5a621f6ab4226965367 (Grep With Context Lines, variant 2 of 2) over an INFERRED spec; qualification unknown.

function solve(lines, target, before, after) {
  const n = lines.length;
  const blocks = [];
  let nextIndex = 0;
  for (let j = 0; j < n; j++) {
    if (!lines[j].includes(target)) continue;
    let start = j - before;
    if (start < 0) start = 0;
    const stop = Math.min(n, j + after + 1);
    if (stop <= nextIndex) continue;
    if (start > nextIndex || blocks.length === 0) blocks.push([]);
    else start = nextIndex;
    const block = blocks[blocks.length - 1];
    for (let i = start; i < stop; i++) block.push(lines[i]);
    nextIndex = stop;
  }
  return blocks;
}

function grepWithContextBlocks(lines, target, before, after) { return solve(lines, target, before, after); }

module.exports = solve;
module.exports.grepWithContextBlocks = grepWithContextBlocks;
