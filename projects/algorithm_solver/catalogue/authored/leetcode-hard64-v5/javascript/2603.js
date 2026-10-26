'use strict';

// 2603. Collect Coins in a Tree. Prune coinless branches and then two complete outer layers; O(n) time and O(n) space. Inputs are preserved.

function solve(coins, edges) {
  const size = coins.length;
  const graph = Array.from({ length: size }, () => []);
  for (const [first, second] of edges) {
    graph[first].push(second);
    graph[second].push(first);
  }
  const degree = graph.map(neighbors => neighbors.length);
  let remaining = edges.length;
  let queue = [];
  for (let node = 0; node < size; node += 1) if (degree[node] === 1 && coins[node] === 0) queue.push(node);
  for (let head = 0; head < queue.length; head += 1) {
    const node = queue[head];
    if (degree[node] === 0) continue;
    degree[node] = 0;
    for (const neighbor of graph[node]) {
      if (degree[neighbor] === 0) continue;
      degree[neighbor] -= 1;
      remaining -= 1;
      if (degree[neighbor] === 1 && coins[neighbor] === 0) queue.push(neighbor);
    }
  }
  queue = [];
  for (let node = 0; node < size; node += 1) if (degree[node] === 1) queue.push(node);
  let head = 0;
  for (let layer = 0; layer < 2; layer += 1) {
    const end = queue.length;
    while (head < end) {
      const node = queue[head++];
      if (degree[node] === 0) continue;
      degree[node] = 0;
      for (const neighbor of graph[node]) {
        if (degree[neighbor] === 0) continue;
        degree[neighbor] -= 1;
        remaining -= 1;
        if (degree[neighbor] === 1) queue.push(neighbor);
      }
    }
  }
  return 2 * remaining;
}

const collectTheCoins = solve;
class Solution {
  collectTheCoins(coins, edges) { return solve(coins, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, collectTheCoins };
