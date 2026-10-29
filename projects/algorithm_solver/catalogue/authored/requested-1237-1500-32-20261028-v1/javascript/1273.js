"use strict";

function solve(nodes, parent, value) {
  const children = Array.from({ length: nodes }, () => []);
  for (let i = 1; i < nodes; i++) children[parent[i]].push(i);
  const order = [];
  const stack = [0];
  while (stack.length > 0) {
    const u = stack.pop();
    order.push(u);
    const ch = children[u];
    for (let i = 0; i < ch.length; i++) stack.push(ch[i]);
  }
  const subSum = value.slice();
  const subCnt = new Int32Array(nodes).fill(1);
  for (let i = order.length - 1; i >= 0; i--) {
    const u = order[i];
    if (subSum[u] === 0) {
      subCnt[u] = 0;
    } else if (parent[u] !== -1) {
      const p = parent[u];
      subSum[p] += subSum[u];
      subCnt[p] += subCnt[u];
    }
  }
  return subCnt[0];
}

function deleteTreeNodes(nodes, parent, value) {
  return solve(nodes, parent, value);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.deleteTreeNodes = deleteTreeNodes;
