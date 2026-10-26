'use strict';

// 1761. Minimum Degree of a Connected Trio in a Graph.
// Enumerate triangles in an adjacency matrix; O(n^3) time, O(n^2) space. Inputs are preserved.

function solve(n, edges) {
  const graph = Array.from({ length: n }, () => new Uint8Array(n));
  const degree = Array(n).fill(0);
  for (const [first, second] of edges) {
    const a = first - 1, b = second - 1;
    graph[a][b] = graph[b][a] = 1;
    degree[a] += 1; degree[b] += 1;
  }
  let answer = Infinity;
  for (let a = 0; a < n; a += 1) {
    for (let b = a + 1; b < n; b += 1) {
      if (!graph[a][b]) continue;
      for (let c = b + 1; c < n; c += 1) if (graph[a][c] && graph[b][c]) answer = Math.min(answer, degree[a] + degree[b] + degree[c] - 6);
    }
  }
  return answer === Infinity ? -1 : answer;
}

const minTrioDegree = solve;
class Solution {
  minTrioDegree(n, edges) { return solve(n, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minTrioDegree };
