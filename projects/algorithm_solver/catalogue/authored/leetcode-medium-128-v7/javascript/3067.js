'use strict';

// 3067. Count Pairs of Connectable Servers in a Weighted Tree Network: combine divisible-distance nodes from distinct branches of each tree root.
// O(n * n) time and O(n) auxiliary space; inputs are read-only.
function solve(edges, signalSpeed) {
  const size = edges.length + 1;
  const graph = Array.from({ length: size }, () => []);
  for (const [left, right, weight] of edges) {
    graph[left].push([right, weight]);
    graph[right].push([left, weight]);
  }
  const result = new Array(size).fill(0);
  for (let root = 0; root < size; root += 1) {
    let previous = 0;
    for (const [child, weight] of graph[root]) {
      let count = 0;
      const stack = [[child, root, weight % signalSpeed]];
      while (stack.length) {
        const [node, parent, distance] = stack.pop();
        if (distance === 0) count += 1;
        for (const [neighbor, edgeWeight] of graph[node]) {
          if (neighbor !== parent) stack.push([neighbor, node, (distance + edgeWeight) % signalSpeed]);
        }
      }
      result[root] += previous * count;
      previous += count;
    }
  }
  return result;
}

const countPairsOfConnectableServers = solve;
class Solution {
  countPairsOfConnectableServers(edges, signalSpeed) { return solve(edges, signalSpeed); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPairsOfConnectableServers };
