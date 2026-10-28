'use strict';

// 909. Snakes and Ladders (Medium).
// Specification: https://leetcode.com/problems/snakes-and-ladders/description/
function solve(board) {
  const n = board.length;
  const cells = [0];
  for (let r = n - 1; r >= 0; r--) {
    const row = (n - 1 - r) % 2 === 0 ? board[r] : board[r].slice().reverse();
    for (const v of row) cells.push(v);
  }
  const target = n * n;
  const dist = new Array(target + 1).fill(-1);
  dist[1] = 0;
  const queue = [1];
  while (queue.length > 0) {
    const current = queue.shift();
    if (current === target) return dist[current];
    for (let step = 1; step <= 6; step++) {
      let next = current + step;
      if (next > target) break;
      if (cells[next] !== -1) next = cells[next];
      if (dist[next] === -1) { dist[next] = dist[current] + 1; queue.push(next); }
    }
  }
  return -1;
}
const snakesAndLadders = solve;
class Solution { snakesAndLadders(board) { return solve(board); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, snakesAndLadders };
