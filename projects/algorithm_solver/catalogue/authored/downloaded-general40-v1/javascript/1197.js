'use strict';

// 1197. Minimum Knight Moves (Medium).
// Specification: https://leetcode.com/problems/minimum-knight-moves/description/
function solve(x, y) {
  const targetX = Math.abs(x); const targetY = Math.abs(y);
  const queue = [[0, 0, 0]];
  const visited = new Set(['0,0']);
  const moves = [[1, 2], [2, 1], [2, -1], [1, -2], [-1, -2], [-2, -1], [-2, 1], [-1, 2]];
  let head = 0;
  while (head < queue.length) {
    const [cx, cy, steps] = queue[head++];
    if (cx === targetX && cy === targetY) return steps;
    for (const [dx, dy] of moves) {
      const nx = cx + dx; const ny = cy + dy;
      const key = `${nx},${ny}`;
      if (nx < -2 || ny < -2 || nx > targetX + 2 || ny > targetY + 2) continue;
      if (!visited.has(key)) { visited.add(key); queue.push([nx, ny, steps + 1]); }
    }
  }
  return -1;
}
const minKnightMoves = solve;
class Solution { minKnightMoves(x, y) { return solve(x, y); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minKnightMoves };
