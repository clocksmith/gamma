'use strict';

// 3004. Maximum Subtree of the Same Color: propagate complete-subtree sizes and color validity in reverse traversal order.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(edges, colors) {
  const adjacency = Array.from({ length: colors.length }, () => []);
  for (const [left, right] of edges) {
    adjacency[left].push(right);
    adjacency[right].push(left);
  }
  const parents = new Int32Array(colors.length).fill(-1);
  const order = [0];
  for (let index = 0; index < order.length; index += 1) {
    const node = order[index];
    for (const neighbor of adjacency[node]) {
      if (neighbor !== parents[node]) {
        parents[neighbor] = node;
        order.push(neighbor);
      }
    }
  }
  const sizes = new Int32Array(colors.length).fill(1);
  const uniform = new Uint8Array(colors.length).fill(1);
  let best = 1;
  for (let index = order.length - 1; index >= 0; index -= 1) {
    const node = order[index];
    if (uniform[node]) best = Math.max(best, sizes[node]);
    const parent = parents[node];
    if (parent !== -1) {
      sizes[parent] += sizes[node];
      if (!uniform[node] || colors[node] !== colors[parent]) uniform[parent] = 0;
    }
  }
  return best;
}

const maximumSubtreeSize = solve;
class Solution {
  maximumSubtreeSize(edges, colors) { return solve(edges, colors); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumSubtreeSize };
