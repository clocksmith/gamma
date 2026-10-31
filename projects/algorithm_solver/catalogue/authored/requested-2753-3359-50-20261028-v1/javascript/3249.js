"use strict";

function solve(edges) {
  const n = edges.length + 1;
  const adj = Array.from({ length: n }, () => []);
  for (let i = 0; i < edges.length; i++) {
    const [u, v] = edges[i];
    adj[u].push(v);
    adj[v].push(u);
  }
  const parent = new Int32Array(n).fill(-1);
  const order = [0];
  for (let i = 0; i < order.length; i++) {
    const u = order[i];
    const nb = adj[u];
    for (let j = 0; j < nb.length; j++) {
      const v = nb[j];
      if (v !== parent[u]) {
        parent[v] = u;
        order.push(v);
      }
    }
  }
  const sz = new Int32Array(n).fill(1);
  let good = 0;
  for (let i = order.length - 1; i >= 0; i--) {
    const u = order[i];
    let first = -1;
    let ok = true;
    const nb = adj[u];
    for (let j = 0; j < nb.length; j++) {
      const v = nb[j];
      if (v !== parent[u]) {
        sz[u] += sz[v];
        if (first === -1) first = sz[v];
        else if (sz[v] !== first) ok = false;
      }
    }
    if (ok) good++;
  }
  return good;
}

function countGoodNodes(edges) {
  return solve(edges);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.countGoodNodes = countGoodNodes;
