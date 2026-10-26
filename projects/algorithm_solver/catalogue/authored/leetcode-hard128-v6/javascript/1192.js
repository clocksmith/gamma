'use strict';

// 1192. Critical Connections in a Network.
// Iterative low-link DFS; O(n + m) time and space. Inputs are preserved.

function solve(n, connections) {
  const graph = Array.from({ length: n }, () => []);
  connections.forEach(([a, b], edge) => {
    graph[a].push([b, edge]);
    graph[b].push([a, edge]);
  });
  const entered = Array(n).fill(-1);
  const low = Array(n).fill(0);
  const parent = Array(n).fill(-1);
  const parentEdge = Array(n).fill(-1);
  const offset = Array(n).fill(0);
  const bridges = [];
  let clock = 0;
  for (let root = 0; root < n; root += 1) {
    if (entered[root] !== -1) continue;
    entered[root] = low[root] = clock++;
    const stack = [root];
    while (stack.length > 0) {
      const node = stack[stack.length - 1];
      if (offset[node] === graph[node].length) {
        stack.pop();
        const previous = parent[node];
        if (previous !== -1) {
          if (low[node] > entered[previous]) bridges.push([previous, node]);
          low[previous] = Math.min(low[previous], low[node]);
        }
        continue;
      }
      const [neighbor, edge] = graph[node][offset[node]++];
      if (edge === parentEdge[node]) continue;
      if (entered[neighbor] !== -1) {
        low[node] = Math.min(low[node], entered[neighbor]);
        continue;
      }
      parent[neighbor] = node;
      parentEdge[neighbor] = edge;
      entered[neighbor] = low[neighbor] = clock++;
      stack.push(neighbor);
    }
  }
  return bridges;
}

const criticalConnections = solve;
class Solution {
  criticalConnections(n, connections) { return solve(n, connections); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, criticalConnections };
