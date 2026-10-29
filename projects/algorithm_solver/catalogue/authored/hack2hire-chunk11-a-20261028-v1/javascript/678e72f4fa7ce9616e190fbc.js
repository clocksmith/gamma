"use strict";
// Hack2Hire 678e72f4fa7ce9616e190fbc (Find Optimal Moves) over an INFERRED spec; qualification unknown.

function solve(arr) {
  let moves = 0, previous = 0;
  for (const v of arr) {
    if (v > previous) moves += v - previous;
    previous = v;
  }
  return moves;
}

function findOptimalMoves(arr) { return solve(arr); }

module.exports = solve;
module.exports.findOptimalMoves = findOptimalMoves;
