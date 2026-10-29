"use strict";
// Hack2Hire 680aa01ecbb5948f87732bc0 (Shortest Path in Unweighted Graph) over an INFERRED spec; qualification unknown.

function solve(n, edges, source, target) {
  if (source === target) return 0;
  const start = new Int32Array(n + 1);
  for (const [u, v] of edges) { start[u + 1]++; start[v + 1]++; }
  for (let i = 0; i < n; i++) start[i + 1] += start[i];
  const fill = Int32Array.from(start), adj = new Int32Array(start[n]);
  for (const [u, v] of edges) { adj[fill[u]++] = v; adj[fill[v]++] = u; }
  const dist = new Int32Array(n).fill(-1), queue = new Int32Array(n);
  dist[source] = 0;
  let head = 0, tail = 0;
  queue[tail++] = source;
  while (head < tail) {
    const u = queue[head++];
    for (let j = start[u]; j < start[u + 1]; j++) {
      const v = adj[j];
      if (dist[v] < 0) {
        dist[v] = dist[u] + 1;
        if (v === target) return dist[v];
        queue[tail++] = v;
      }
    }
  }
  return -1;
}

function shortestPath(n, edges, source, target) { return solve(n, edges, source, target); }

module.exports = solve;
module.exports.shortestPath = shortestPath;
