"use strict";
// Hack2Hire 6910bee571ea59cda5a81a94 (Minimum Root-to-Leaf Path Sum) over an INFERRED spec; qualification unknown.

function solve(root) {
  if (root.length === 0) return [];
  const values = [root[0]], left = [-1], right = [-1];
  let head = 0, i = 1;
  while (i < root.length) {
    const node = head++;
    if (root[i] !== null) { values.push(root[i]); left.push(-1); right.push(-1); left[node] = values.length - 1; }
    i++;
    if (i < root.length) {
      if (root[i] !== null) { values.push(root[i]); left.push(-1); right.push(-1); right[node] = values.length - 1; }
      i++;
    }
  }
  const parent = new Array(values.length).fill(-1);
  const total = new Array(values.length).fill(0);
  total[0] = values[0];
  let best = -1;
  const stack = [0];
  while (stack.length) {
    const node = stack.pop();
    if (left[node] === -1 && right[node] === -1) {
      if (best === -1 || total[node] < total[best]) best = node;
      continue;
    }
    for (const child of [right[node], left[node]]) {
      if (child !== -1) {
        parent[child] = node;
        total[child] = total[node] + values[child];
        stack.push(child);
      }
    }
  }
  const path = [];
  while (best !== -1) { path.push(values[best]); best = parent[best]; }
  return path.reverse();
}

function minPathSum(root) { return solve(root); }

module.exports = solve;
module.exports.minPathSum = minPathSum;
