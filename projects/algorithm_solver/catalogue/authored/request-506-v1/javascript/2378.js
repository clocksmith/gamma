// Original implementation. Contract: https://leetcode.com/problems/choose-edges-to-maximize-score-in-a-tree/
"use strict";

function solve(edges) {
  const n = edges.length;
  const children = Array.from({ length: n }, () => []);
  for (let node = 1; node < n; node++) {
    const [parent, weight] = edges[node];
    children[parent].push([node, weight]);
  }
  const order = [0];
  for (let index = 0; index < order.length; index++) {
    for (const [child] of children[order[index]]) order.push(child);
  }
  // blocked[node] forbids matching this node with a child (parent edge selected).
  const free = Array(n).fill(0);
  const blocked = Array(n).fill(0);
  for (let index = order.length - 1; index >= 0; index--) {
    const node = order[index];
    let base = 0;
    let bestGain = 0;
    for (const [child, weight] of children[node]) {
      base += free[child];
      bestGain = Math.max(bestGain, weight + blocked[child] - free[child]);
    }
    blocked[node] = base;
    free[node] = base + bestGain;
  }
  return free[0];
}

module.exports = solve;
