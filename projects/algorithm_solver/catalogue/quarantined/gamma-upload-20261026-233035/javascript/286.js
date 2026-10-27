'use strict';
// 286. Walls and Gates.
function solve(rooms) {
  const rows = rooms.length; const columns = rooms[0].length; const queue = [];
  for (let row = 0; row < rows; row += 1) for (let column = 0; column < columns; column += 1) {
    if (rooms[row][column] === 0) queue.push([row, column]);
  }
  for (let head = 0; head < queue.length; head += 1) {
    const [row, column] = queue[head];
    for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const nr = row + dr; const nc = column + dc;
      if (nr >= 0 && nr < rows && nc >= 0 && nc < columns && rooms[nr][nc] === 2147483647) {
        rooms[nr][nc] = rooms[row][column] + 1; queue.push([nr, nc]);
      }
    }
  }
}
const wallsAndGates = solve;
class Solution { wallsAndGates(rooms) { solve(rooms); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, wallsAndGates };
