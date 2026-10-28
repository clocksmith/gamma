'use strict';

// 773. Sliding Puzzle (Hard).
// Specification: https://leetcode.com/problems/sliding-puzzle/description/
function solve(board) {
  const start = board.flat().join('');
  const target = '123450';
  const neighbors = [[1, 3], [0, 2, 4], [1, 5], [0, 4], [1, 3, 5], [2, 4]];
  let queue = [start];
  const visited = new Set([start]);
  let steps = 0;
  while (queue.length > 0) {
    const nextQueue = [];
    for (const current of queue) {
      if (current === target) return steps;
      const zero = current.indexOf('0');
      for (const neighbor of neighbors[zero]) {
        const chars = [...current];
        const tmp = chars[zero]; chars[zero] = chars[neighbor]; chars[neighbor] = tmp;
        const candidate = chars.join('');
        if (!visited.has(candidate)) { visited.add(candidate); nextQueue.push(candidate); }
      }
    }
    queue = nextQueue;
    steps++;
  }
  return -1;
}
const slidingPuzzle = solve;
class Solution { slidingPuzzle(board) { return solve(board); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, slidingPuzzle };
