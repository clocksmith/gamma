'use strict';

// 3373. Maximize the Number of Target Nodes After Connecting Trees II: bipartition parity counts in each tree.
// O(n + m) time and O(n + m) space. Inputs are preserved.
function solve(edges1, edges2) {
  function coloring(edges) {
    const n = edges.length + 1;
    const graph = Array.from({ length: n }, () => []);
    for (const [first, second] of edges) {
      graph[first].push(second);
      graph[second].push(first);
    }
    const colors = new Int8Array(n).fill(-1);
    colors[0] = 0;
    const counts = [1, 0];
    const queue = [0];
    for (let head = 0; head < queue.length; head += 1) {
      const node = queue[head];
      for (const neighbor of graph[node]) {
        if (colors[neighbor] === -1) {
          colors[neighbor] = colors[node] ^ 1;
          counts[colors[neighbor]] += 1;
          queue.push(neighbor);
        }
      }
    }
    return [colors, counts];
  }
  const [colors, counts] = coloring(edges1);
  const [, other] = coloring(edges2);
  const extra = edges2.length > 0 ? Math.max(other[0], other[1]) : 0;
  return Array.from(colors, color => counts[color] + extra);
}

const maxTargetNodes = solve;
class Solution {
  maxTargetNodes(edges1, edges2) { return solve(edges1, edges2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxTargetNodes };
