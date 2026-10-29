"use strict";

function solve(edges) {
  if (!edges || edges.length === 0) return 0;
  const n = edges.length + 1;
  const adj = Array.from({ length: n }, () => []);
  for (let i = 0; i < edges.length; i++) {
    const [u, v] = edges[i];
    adj[u].push(v);
    adj[v].push(u);
  }
  const farthest = (start) => {
    const dist = new Int32Array(n).fill(-1);
    dist[start] = 0;
    const q = [start];
    let head = 0, far = start;
    while (head < q.length) {
      const u = q[head++];
      if (dist[u] > dist[far]) far = u;
      const nb = adj[u];
      for (let i = 0; i < nb.length; i++) {
        const v = nb[i];
        if (dist[v] === -1) {
          dist[v] = dist[u] + 1;
          q.push(v);
        }
      }
    }
    return [far, dist[far]];
  };
  const [u] = farthest(0);
  return farthest(u)[1];
}

function treeDiameter(edges) {
  return solve(edges);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.treeDiameter = treeDiameter;
