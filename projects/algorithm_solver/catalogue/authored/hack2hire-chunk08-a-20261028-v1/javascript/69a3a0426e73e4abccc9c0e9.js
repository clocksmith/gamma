"use strict";
// Hack2Hire 69a3a0426e73e4abccc9c0e9 (Reach End in Grid With Teleports) over an INFERRED spec; qualification unknown.

function solve(grid, teleports) {
  const n = grid.length, m = grid[0].length, jump = new Map();
  for (const [r1, c1, r2, c2] of teleports) jump.set(r1 * m + c1, r2 * m + c2);
  const seen = new Uint8Array(n * m), destination = n * m - 1;
  seen[0] = 1;
  let position = 0, moves = 0;
  while (position !== destination) {
    const r = Math.floor(position / m), c = position - r * m;
    if (c === m - 1 || grid[r][c + 1] === 1) return -1;
    position += 1;
    if (jump.has(position)) position = jump.get(position);
    moves += 1;
    if (seen[position]) return -1;
    seen[position] = 1;
  }
  return moves;
}

function reachEnd(grid, teleports) { return solve(grid, teleports); }

module.exports = solve;
module.exports.reachEnd = reachEnd;
