'use strict';

// 3203. Find Minimum Diameter After Merging Two Trees.
// Connect tree centers after computing both diameters with BFS; O(n+m) time and space. Inputs are preserved.

function solve(edges1, edges2) {
  function diameter(edges) {
    const graph = Array.from({ length: edges.length + 1 }, () => []);
    for (const [a, b] of edges) { graph[a].push(b); graph[b].push(a); }
    function farthest(start) {
      const distance = Array(graph.length).fill(-1), queue = [start]; distance[start] = 0;
      for (let head = 0; head < queue.length; head += 1) {
        const node = queue[head];
        for (const neighbor of graph[node]) if (distance[neighbor] === -1) { distance[neighbor] = distance[node] + 1; queue.push(neighbor); }
      }
      const last = queue[queue.length - 1];
      return [last, distance[last]];
    }
    return farthest(farthest(0)[0])[1];
  }
  const first = diameter(edges1), second = diameter(edges2);
  return Math.max(first, second, Math.ceil(first / 2) + Math.ceil(second / 2) + 1);
}

const minimumDiameterAfterMerge = solve;
class Solution {
  minimumDiameterAfterMerge(edges1, edges2) { return solve(edges1, edges2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumDiameterAfterMerge };
