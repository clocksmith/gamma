"use strict";

function solve(parent, s) {
  const n = parent.length;
  const children = Array.from({ length: n }, () => []);
  for (let i = 1; i < n; i++) children[parent[i]].push(i);
  const newParent = parent.slice();
  const lastSeen = new Int32Array(26).fill(-1);

  function dfs(u) {
    const code = s.charCodeAt(u) - 97;
    const prev = lastSeen[code];
    if (prev !== -1) newParent[u] = prev;
    lastSeen[code] = u;
    const ch = children[u];
    for (let i = 0; i < ch.length; i++) dfs(ch[i]);
    lastSeen[code] = prev;
  }

  dfs(0);
  const newChildren = Array.from({ length: n }, () => []);
  for (let i = 1; i < n; i++) newChildren[newParent[i]].push(i);
  const order = [0];
  for (let i = 0; i < order.length; i++) {
    const u = order[i];
    const ch = newChildren[u];
    for (let j = 0; j < ch.length; j++) order.push(ch[j]);
  }
  const sz = new Array(n).fill(1);
  for (let i = order.length - 1; i >= 0; i--) {
    const u = order[i];
    if (u !== 0) sz[newParent[u]] += sz[u];
  }
  return sz;
}

function findSubtreeSizes(parent, s) {
  return solve(parent, s);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.findSubtreeSizes = findSubtreeSizes;
