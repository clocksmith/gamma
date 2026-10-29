"use strict";
// Hack2Hire 6a73bf2fd713d873ca7a77c6 (Largest Consecutive Skill Team) over an INFERRED spec; qualification unknown.

function solve(skills) {
  const count = new Map();
  for (const s of skills) count.set(s, (count.get(s) || 0) + 1);
  let best = 0;
  for (const level of count.keys()) {
    if (count.has(level - 1)) continue;
    let size = 0, current = level;
    while (count.has(current)) { size += count.get(current); current++; }
    if (size > best) best = size;
  }
  return best;
}

function largestTeam(skills) { return solve(skills); }

module.exports = solve;
module.exports.largestTeam = largestTeam;
