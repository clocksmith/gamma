'use strict';

// 2061. Number of Spaces Cleaning Robot Cleaned: stop at the first repeated position-and-direction state.
// O(r * c) time and O(r * c) auxiliary space; inputs are read-only.
function solve(room) {
  const rows = room.length;
  const columns = room[0].length;
  const states = new Uint8Array(rows * columns);
  const directions = [[0, 1], [1, 0], [0, -1], [-1, 0]];
  let row = 0;
  let column = 0;
  let direction = 0;
  let cleaned = 0;
  while (true) {
    const index = row * columns + column;
    const bit = 1 << direction;
    if ((states[index] & bit) !== 0) return cleaned;
    if (states[index] === 0) cleaned += 1;
    states[index] |= bit;
    const nextRow = row + directions[direction][0];
    const nextColumn = column + directions[direction][1];
    if (nextRow >= 0 && nextRow < rows && nextColumn >= 0 && nextColumn < columns && room[nextRow][nextColumn] === 0) {
      row = nextRow;
      column = nextColumn;
    } else direction = (direction + 1) % 4;
  }
}

const numberOfCleanRooms = solve;
class Solution {
  numberOfCleanRooms(room) { return solve(room); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfCleanRooms };
