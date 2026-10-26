'use strict';

// 2850. Minimum Moves to Spread Stones Over Grid: assign each surplus stone to an empty cell with subset dynamic programming.
// O(z * 2^z) time and O(2^z) auxiliary space, where z is the number of empty cells; inputs are read-only.
function solve(grid) {
  const surplus = [];
  const empty = [];
  for (let row = 0; row < 3; row += 1) {
    for (let column = 0; column < 3; column += 1) {
      if (grid[row][column] === 0) empty.push([row, column]);
      else {
        for (let stone = 1; stone < grid[row][column]; stone += 1) surplus.push([row, column]);
      }
    }
  }
  const size = empty.length;
  const best = new Array(1 << size).fill(Infinity);
  const bits = new Uint8Array(1 << size);
  for (let mask = 1; mask < bits.length; mask += 1) bits[mask] = bits[mask >> 1] + (mask & 1);
  best[0] = 0;
  for (let mask = 0; mask + 1 < best.length; mask += 1) {
    const [row, column] = surplus[bits[mask]];
    for (let index = 0; index < size; index += 1) {
      const bit = 1 << index;
      if ((mask & bit) !== 0) continue;
      const target = mask | bit;
      const distance = Math.abs(row - empty[index][0]) + Math.abs(column - empty[index][1]);
      best[target] = Math.min(best[target], best[mask] + distance);
    }
  }
  return best[best.length - 1];
}

const minimumMoves = solve;
class Solution {
  minimumMoves(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumMoves };
