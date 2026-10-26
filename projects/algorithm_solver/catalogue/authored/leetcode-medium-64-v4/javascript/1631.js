'use strict';

// 1631. Path With Minimum Effort: join grid edges by increasing effort until the corners become connected.
// O(r * c * log(r * c + 1)) time and O(r * c) auxiliary space; inputs are read-only.
function solve(heights) {
  const rows = heights.length;
  const cols = heights[0].length;
  const count = rows * cols;
  if (count === 1) return 0;
  const edges = [];
  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      const node = row * cols + col;
      if (row + 1 < rows) edges.push([Math.abs(heights[row][col] - heights[row + 1][col]), node, node + cols]);
      if (col + 1 < cols) edges.push([Math.abs(heights[row][col] - heights[row][col + 1]), node, node + 1]);
    }
  }
  edges.sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);
  const parent = Int32Array.from({ length: count }, (_, index) => index);
  const size = new Int32Array(count).fill(1);
  function find(node) {
    while (parent[node] !== node) {
      parent[node] = parent[parent[node]];
      node = parent[node];
    }
    return node;
  }
  for (const [effort, first, second] of edges) {
    let firstRoot = find(first);
    let secondRoot = find(second);
    if (firstRoot !== secondRoot) {
      if (size[firstRoot] < size[secondRoot]) [firstRoot, secondRoot] = [secondRoot, firstRoot];
      parent[secondRoot] = firstRoot;
      size[firstRoot] += size[secondRoot];
    }
    if (find(0) === find(count - 1)) return effort;
  }
  return 0;
}

const minimumEffortPath = solve;
class Solution {
  minimumEffortPath(heights) { return solve(heights); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumEffortPath };
