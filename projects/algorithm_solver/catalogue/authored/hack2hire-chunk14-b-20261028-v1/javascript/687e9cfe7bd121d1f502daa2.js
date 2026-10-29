"use strict";
// Hack2Hire 687e9cfe7bd121d1f502daa2 (Block-Based String Assembly) over an INFERRED spec; qualification unknown.

function solve(blocks, target) {
  if (target.length > blocks.length) return false;
  const holders = new Map();
  blocks.forEach((block, b) => {
    for (const letter of new Set(block)) {
      if (!holders.has(letter)) holders.set(letter, []);
      holders.get(letter).push(b);
    }
  });
  const owner = new Array(blocks.length).fill(-1);
  const augment = (position, seen) => {
    for (const b of holders.get(target[position]) || []) {
      if (seen[b]) continue;
      seen[b] = true;
      if (owner[b] < 0 || augment(owner[b], seen)) { owner[b] = position; return true; }
    }
    return false;
  };
  for (let position = 0; position < target.length; position++) {
    if (!augment(position, new Array(blocks.length).fill(false))) return false;
  }
  return true;
}

function canAssemble(blocks, target) { return solve(blocks, target); }

module.exports = solve;
module.exports.canAssemble = canAssemble;
