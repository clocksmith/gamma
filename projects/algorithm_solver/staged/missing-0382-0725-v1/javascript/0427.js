'use strict';

// 427. Construct Quad Tree. Prefix sums identify uniform quadrants; input grid is preserved.

class Node {
  constructor(val = false, isLeaf = false, topLeft = null, topRight = null,
              bottomLeft = null, bottomRight = null) {
    this.val = val;
    this.isLeaf = isLeaf;
    this.topLeft = topLeft;
    this.topRight = topRight;
    this.bottomLeft = bottomLeft;
    this.bottomRight = bottomRight;
  }
}

function solve(grid) {
  const n = grid.length;
  const prefix = Array.from({length: n + 1}, () => Array(n + 1).fill(0));
  for (let r = 0; r < n; r += 1) for (let c = 0; c < n; c += 1) {
    prefix[r + 1][c + 1] = grid[r][c] + prefix[r][c + 1] + prefix[r + 1][c] - prefix[r][c];
  }
  function build(r, c, size) {
    const total = prefix[r + size][c + size] - prefix[r][c + size] - prefix[r + size][c] + prefix[r][c];
    if (total === 0 || total === size * size) return new Node(total !== 0, true);
    const half = size / 2;
    return new Node(false, false, build(r, c, half), build(r, c + half, half),
      build(r + half, c, half), build(r + half, c + half, half));
  }
  return build(0, 0, n);
}

const construct = solve;
class Solution {
  construct(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, construct };
