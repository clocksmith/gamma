// Original hack2hire:691614103f8671d8f7a56642; inferred public-preview contract; qualification unknown.
"use strict";
function clusterSummary(parents) {
  const n = parents.length;
  if (!n) return {count: 0, topology: ''};
  const children = Array.from({length:n}, () => []), counts = Array(n).fill(1), topology = Array(n).fill('');
  let root;
  parents.forEach((p, node) => { if (p === -1) root = node; else children[p].push(node); });
  const pending = children.map(row => row.length), queue = [];
  for (let i = 0; i < n; i++) if (!pending[i]) queue.push(i);
  for (let head = 0; head < queue.length; head++) {
    const node = queue[head], parent = parents[node];
    topology[node] = String(node) + (children[node].length ? '(' + children[node].map(c => topology[c]).join(',') + ')' : '');
    if (parent >= 0) { counts[parent] += counts[node]; if (--pending[parent] === 0) queue.push(parent); }
  }
  return {count: counts[root], topology: topology[root]};
}

const solve = clusterSummary;
module.exports = solve;
module.exports.clusterSummary = clusterSummary;
module.exports.Solution = class { clusterSummary(...args) { return clusterSummary(...args); } };
