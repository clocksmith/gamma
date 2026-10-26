'use strict';

// 3812. Minimum Edge Toggles on a Tree.
// O(n) time and space; unique edge-parity solution in a tree, emitted in increasing index order.
function solve(n, edges, start, target) {
  const graph = Array.from({ length: n }, () => []);
  for (let index = 0; index < edges.length; index += 1) {
    const [left, right] = edges[index];
    graph[left].push([right, index]);
    graph[right].push([left, index]);
  }
  const parent = Array(n).fill(-1);
  const parentEdge = Array(n).fill(-1);
  const order = [0];
  for (let cursor = 0; cursor < order.length; cursor += 1) {
    const node = order[cursor];
    for (const [child, edge] of graph[node]) {
      if (child === parent[node]) continue;
      parent[child] = node;
      parentEdge[child] = edge;
      order.push(child);
    }
  }
  const parity = Array.from({ length: n }, (_, index) => Number(start[index] !== target[index]));
  const selected = Array(n - 1).fill(false);
  for (let index = order.length - 1; index > 0; index -= 1) {
    const node = order[index];
    if (parity[node]) {
      selected[parentEdge[node]] = true;
      parity[parent[node]] ^= 1;
    }
  }
  if (parity[0]) return [-1];
  const result = [];
  for (let edge = 0; edge < selected.length; edge += 1) if (selected[edge]) result.push(edge);
  return result;
}

const minimumFlips = solve;
class Solution {
  minimumFlips(n, edges, start, target) { return solve(n, edges, start, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumFlips };
