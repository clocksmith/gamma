'use strict';

// 3459. Length of Longest V-Shaped Diagonal Segment: join a one-starting prefix with a clockwise alternating diagonal suffix.
// O(rows*columns) time and O(rows*columns) auxiliary space. Inputs are preserved.
function solve(grid) {
  const rows = grid.length;
  const columns = grid[0].length;
  const directions = [[1, 1], [1, -1], [-1, -1], [-1, 1]];
  const tails = [];
  for (const [dx, dy] of directions) {
    const tail = new Uint16Array(rows * columns);
    const start = dx > 0 ? rows - 1 : 0;
    const stop = dx > 0 ? -1 : rows;
    for (let row = start; row !== stop; row -= dx) {
      for (let column = 0; column < columns; column += 1) {
        const index = row * columns + column;
        tail[index] = 1;
        const followingRow = row + dx;
        const followingColumn = column + dy;
        const expected = grid[row][column] === 1 ? 2 : 2 - grid[row][column];
        if (followingRow >= 0 && followingRow < rows && followingColumn >= 0
          && followingColumn < columns && grid[followingRow][followingColumn] === expected) {
          tail[index] += tail[followingRow * columns + followingColumn];
        }
      }
    }
    tails.push(tail);
  }
  let answer = 0;
  for (let direction = 0; direction < 4; direction += 1) {
    const [dx, dy] = directions[direction];
    const prefix = new Uint16Array(rows * columns);
    const start = dx > 0 ? 0 : rows - 1;
    const stop = dx > 0 ? rows : -1;
    for (let row = start; row !== stop; row += dx) {
      for (let column = 0; column < columns; column += 1) {
        const index = row * columns + column;
        if (grid[row][column] === 1) {
          prefix[index] = 1;
        } else {
          const previousRow = row - dx;
          const previousColumn = column - dy;
          if (previousRow >= 0 && previousRow < rows && previousColumn >= 0 && previousColumn < columns) {
            const previousIndex = previousRow * columns + previousColumn;
            const previousValue = grid[previousRow][previousColumn];
            const expected = previousValue === 1 ? 2 : 2 - previousValue;
            if (prefix[previousIndex] > 0 && grid[row][column] === expected) prefix[index] = prefix[previousIndex] + 1;
          }
        }
        if (prefix[index] > 0) answer = Math.max(answer, prefix[index] + tails[(direction + 1) % 4][index] - 1);
      }
    }
  }
  return answer;
}

const lenOfVDiagonal = solve;
class Solution {
  lenOfVDiagonal(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, lenOfVDiagonal };
