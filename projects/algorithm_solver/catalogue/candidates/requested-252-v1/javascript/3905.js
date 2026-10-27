/**
 * 3905. Multi Source Flood Fill
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/multi-source-flood-fill/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3905.Multi%20Source%20Flood%20Fill/README_EN.md
 * Complexity: O(n*m) time and space.
 * Simultaneous rounds; maximum color wins same-round ties. Distinct initial source cells. Sources preserved.
 */

function solve(n, m, sources) {
  const grid = Array.from({ length: n }, () => Array(m).fill(0));
  let frontier = [];
  for (const [row, column, color] of sources) {
    grid[row][column] = color;
    frontier.push(row * m + column);
  }
  const directions = [[-1, 0], [1, 0], [0, -1], [0, 1]];
  while (frontier.length) {
    const pending = new Map();
    for (const position of frontier) {
      const row = Math.floor(position / m);
      const column = position % m;
      for (const [dr, dc] of directions) {
        const nextRow = row + dr;
        const nextColumn = column + dc;
        if (nextRow < 0 || nextRow >= n || nextColumn < 0 || nextColumn >= m || grid[nextRow][nextColumn] !== 0) continue;
        const key = nextRow * m + nextColumn;
        pending.set(key, Math.max(pending.get(key) || 0, grid[row][column]));
      }
    }
    frontier = [...pending.keys()];
    for (const [position, color] of pending) grid[Math.floor(position / m)][position % m] = color;
  }
  return grid;
}

function colorGrid(n, m, sources) {
  return solve(n, m, sources);
}

class Solution {
  colorGrid(n, m, sources) {
    return solve(n, m, sources);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, colorGrid, Solution };
}
