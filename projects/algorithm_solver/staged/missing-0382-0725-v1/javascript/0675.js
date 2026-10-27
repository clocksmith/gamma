'use strict';

// 675. Cut Off Trees for Golf Event. Visit trees by increasing height with shortest grid paths; input forest is preserved.

function solve(forest) {
  const rows = forest.length, cols = forest[0].length, trees = [];
  for (let r = 0; r < rows; r += 1) for (let c = 0; c < cols; c += 1) if (forest[r][c] > 1) trees.push([forest[r][c], r, c]);
  trees.sort((a, b) => a[0] - b[0]);
  if (trees.length > 0 && forest[0][0] === 0) return -1;
  function distance(source, target) {
    const queue = [[source[0], source[1], 0]], seen = new Set([source[0] * cols + source[1]]);
    for (let head = 0; head < queue.length; head += 1) {
      const [r, c, steps] = queue[head];
      if (r === target[0] && c === target[1]) return steps;
      for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nr = r + dr, nc = c + dc, key = nr * cols + nc;
        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && forest[nr][nc] > 0 && !seen.has(key)) {
          seen.add(key); queue.push([nr, nc, steps + 1]);
        }
      }
    }
    return -1;
  }
  let current = [0, 0], total = 0;
  for (const [, row, col] of trees) {
    const target = [row, col], steps = distance(current, target);
    if (steps < 0) return -1;
    total += steps; current = target;
  }
  return total;
}

const cutOffTree = solve;
class Solution {
  cutOffTree(forest) { return solve(forest); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, cutOffTree };
