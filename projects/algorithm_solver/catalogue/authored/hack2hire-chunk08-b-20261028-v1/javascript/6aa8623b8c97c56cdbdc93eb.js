"use strict";
// Hack2Hire 6aa8623b8c97c56cdbdc93eb (Tetris Block Drop) over an INFERRED spec; qualification unknown.

function land(background, block, offset) {
  const rows = background.length, h = block.length, w = block[0].length;
  let drop = Infinity;
  for (let j = 0; j < w; j++) {
    let lowest = -1;
    for (let r = 0; r < h; r++) if (block[r][j]) lowest = r;
    if (lowest < 0) continue;
    let first = rows;
    for (let r = 0; r < rows; r++) if (background[r][offset + j]) { first = r; break; }
    drop = Math.min(drop, first - 1 - lowest);
  }
  const grid = background.map((row) => row.slice());
  for (let r = 0; r < h; r++) for (let j = 0; j < w; j++) if (block[r][j]) grid[drop + r][offset + j] = 1;
  return grid;
}

function solve(background, block, offset) {
  const grid = land(background, block, offset), width = grid[0].length;
  const kept = grid.filter((row) => !row.every((v) => v === 1));
  const out = [];
  for (let i = kept.length; i < grid.length; i++) out.push(new Array(width).fill(0));
  return out.concat(kept);
}

function dropBlockAndClear(background, block, offset) { return solve(background, block, offset); }

module.exports = solve;
module.exports.dropBlockAndClear = dropBlockAndClear;
