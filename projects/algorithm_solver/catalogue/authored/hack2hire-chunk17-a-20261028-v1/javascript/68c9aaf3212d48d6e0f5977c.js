"use strict";
// Hack2Hire 68c9aaf3212d48d6e0f5977c (Thrilling Teleporters, variant 1 of 2) over an INFERRED spec; qualification unknown.

function solve(teleporters, dieSides, currentSquare, lastSquare) {
  const jump = new Map();
  for (const entry of teleporters) {
    const comma = entry.indexOf(",");
    jump.set(Number(entry.slice(0, comma)), Number(entry.slice(comma + 1)));
  }
  const ends = new Set();
  for (let roll = 1; roll <= dieSides; roll++) {
    const land = currentSquare + roll;
    ends.add(land >= lastSquare ? lastSquare : (jump.has(land) ? jump.get(land) : land));
  }
  return Array.from(ends).sort((a, b) => a - b);
}

function possibleDestinations(teleporters, dieSides, currentSquare, lastSquare) { return solve(teleporters, dieSides, currentSquare, lastSquare); }

module.exports = solve;
module.exports.possibleDestinations = possibleDestinations;
