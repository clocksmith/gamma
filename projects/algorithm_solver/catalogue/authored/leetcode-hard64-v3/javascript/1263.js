'use strict';

// 1263. Minimum Moves to Move a Box to Their Target Location: BFS over pushes with player reachability; O((rows*columns)^2) time and O(rows*columns) space.

function solve(grid) {
  const rows = grid.length;
  const columns = grid[0].length;
  const cells = rows * columns;
  let player = -1;
  let box = -1;
  let target = -1;
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      const cell = row * columns + column;
      if (grid[row][column] === 'S') player = cell;
      else if (grid[row][column] === 'B') box = cell;
      else if (grid[row][column] === 'T') target = cell;
    }
  }
  const directions = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  function step(cell, dr, dc) {
    const row = Math.floor(cell / columns) + dr;
    const column = cell % columns + dc;
    if (row < 0 || row >= rows || column < 0 || column >= columns || grid[row][column] === '#') return -1;
    return row * columns + column;
  }
  const queue = [[box, player, 0]];
  const seen = new Set([box * cells + player]);
  for (let head = 0; head < queue.length; head += 1) {
    const [currentBox, currentPlayer, pushes] = queue[head];
    if (currentBox === target) return pushes;
    const reachable = new Set([currentPlayer]);
    const walking = [currentPlayer];
    for (let walkHead = 0; walkHead < walking.length; walkHead += 1) {
      for (const [dr, dc] of directions) {
        const neighbor = step(walking[walkHead], dr, dc);
        if (neighbor !== -1 && neighbor !== currentBox && !reachable.has(neighbor)) {
          reachable.add(neighbor);
          walking.push(neighbor);
        }
      }
    }
    for (const [dr, dc] of directions) {
      const destination = step(currentBox, dr, dc);
      const standing = step(currentBox, -dr, -dc);
      if (destination === -1 || !reachable.has(standing)) continue;
      const key = destination * cells + currentBox;
      if (!seen.has(key)) {
        seen.add(key);
        queue.push([destination, currentBox, pushes + 1]);
      }
    }
  }
  return -1;
}

const minPushBox = solve;
class Solution {
  minPushBox(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minPushBox };
