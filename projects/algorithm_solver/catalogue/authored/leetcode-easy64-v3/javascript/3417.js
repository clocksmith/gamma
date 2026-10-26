'use strict';

// 3417. Zigzag Grid Traversal With Skip (Easy).
// Specification: https://leetcode.com/problems/zigzag-grid-traversal-with-skip/description/
// O(rows * columns) time and output space; skipping continues across row boundaries.
function solve(grid) {
  const result = [];
  const columns = grid[0].length;
  let take = true;
  for (let row = 0; row < grid.length; row++) {
    for (let offset = 0; offset < columns; offset++) {
      const column = row % 2 === 0 ? offset : columns - 1 - offset;
      if (take) result.push(grid[row][column]);
      take = !take;
    }
  }
  return result;
}

const zigzagTraversal = solve;
class Solution {
  zigzagTraversal(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, zigzagTraversal };
