"use strict";

function solve(edges) {
  const n = edges.length + 1;
  const adj = Array.from({ length: n }, () => []);
  for (let i = 0; i < edges.length; i++) {
    const [u, v] = edges[i];
    adj[u].push(v);
    adj[v].push(u);
  }
  function bfs(start) {
    const dist = new Int32Array(n).fill(-1);
    const q = new Int32Array(n);
    let head = 0, tail = 0;
    dist[start] = 0;
    q[tail++] = start;
    let last = start;
    while (head < tail) {
      const u = q[head++];
      last = u;
      const nb = adj[u];
      for (let i = 0; i < nb.length; i++) {
        const v = nb[i];
        if (dist[v] === -1) {
          dist[v] = dist[u] + 1;
          q[tail++] = v;
        }
      }
    }
    return [last, dist];
  }
  const [a] = bfs(0);
  const [b, da] = bfs(a);
  const [, db] = bfs(b);
  const out = new Array(n);
  for (let i = 0; i < n; i++) out[i] = da[i] >= db[i] ? a : b;
  return out;
}

function lastMarkedNodes(edges) {
  return solve(edges);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.lastMarkedNodes = lastMarkedNodes;
