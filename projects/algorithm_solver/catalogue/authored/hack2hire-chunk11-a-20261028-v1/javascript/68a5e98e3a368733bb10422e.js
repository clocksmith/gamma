"use strict";
// Hack2Hire 68a5e98e3a368733bb10422e (Find Path with Minimal Bottleneck) over an INFERRED spec; qualification unknown.

function solve(n, edges, k) {
  const weights = [...new Set(edges.map((e) => e[2]))].sort((a, b) => a - b);
  const adjacency = Array.from({ length: n + 1 }, () => []);
  for (const [u, v, w] of edges) { adjacency[u].push(v, w); adjacency[v].push(u, w); }
  const reachable = (limit) => { // breadth-first search over edges not heavier than limit, at most k hops
    const dist = new Array(n + 1).fill(-1);
    dist[1] = 0;
    const queue = [1];
    for (let i = 0; i < queue.length; i++) {
      const x = queue[i];
      if (dist[x] === k) continue;
      const list = adjacency[x];
      for (let j = 0; j < list.length; j += 2) {
        const y = list[j];
        if (list[j + 1] <= limit && dist[y] < 0) {
          if (y === n) return true;
          dist[y] = dist[x] + 1;
          queue.push(y);
        }
      }
    }
    return false;
  };
  let lo = 0, hi = weights.length - 1, answer = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (reachable(weights[mid])) { answer = weights[mid]; hi = mid - 1; } else lo = mid + 1;
  }
  return answer;
}

function findMinimalBottleneck(n, edges, k) { return solve(n, edges, k); }

module.exports = solve;
module.exports.findMinimalBottleneck = findMinimalBottleneck;
